"""
Base class for deriving trainable modules
"""

# global
import os
import abc
import logging

# local
import ivy
from ivy.core.container import Container


# Base #
# -----#

class Module(abc.ABC):

    def __init__(self, dev_str=None, v=None, build_mode='on_init', compile_on_next_step=False, store_vars=True,
                 stateful=None, arg_stateful_idxs=None, kwarg_stateful_idxs=None, fallback_to_non_compiled=False,
                 dev_strs=None):
        """
        Initialze Ivy layer, which is a stateful object consisting of trainable variables.

        :param dev_str: device on which to create the module's variables 'cuda:0', 'cuda:1', 'cpu' etc.
        :type dev_str: str, optional
        :param v: Ivy container of trainable variables. Created internally by default.
        :type v: ivy container, optional
        :param build_mode: How the Module is built, either on initialization (now), explicitly by the user by calling
                           build(), or the first time the __call__ method is run. Default is on initialization.
        :type build_mode: str, optional
        :param compile_on_next_step: Whether to compile the network on the next forward pass. Default is False.
        :type compile_on_next_step: bool, optional
        :param store_vars: Whether or not to store the variables created. Default is True.
        :type store_vars: bool, optional
        :param stateful: The constant id stateful items to track as part of the forward pass.
                         Used when graph compiling, default is None.
        :type stateful: seq of any, optional
        :param arg_stateful_idxs: The nested argument indices of stateful items to track as part of the forward pass.
                                  Used when graph compiling, default is None.
        :type arg_stateful_idxs: seq of any, optional
        :param kwarg_stateful_idxs: The nested keyword argument indices of stateful items to track as part of the
                                    forward pass. Used when graph compiling, default is None.
        :type kwarg_stateful_idxs: seq of any, optional
        :param fallback_to_non_compiled: Whether to fall back to non-compiled forward call in the case that an error is
                                         raised during the compiled forward pass. Default is True.
        :type fallback_to_non_compiled: bool, optional
        :param dev_strs: devices on which to distribute the module's variables 'cuda:0', 'cuda:1', 'cpu' etc.
        :type dev_strs: sequence of str, optional
        :type build_mode: str, optional
        """
        valid_build_modes = ['on_init', 'explicit', 'on_call']
        if build_mode not in valid_build_modes:
            raise Exception('build_mode must be one of {} of type str, but found {} of type{}'.format(
                valid_build_modes, build_mode, type(build_mode)))
        self._dev_str = ivy.default(dev_str, ivy.default(lambda: dev_strs[0], ivy.default_device(), True))
        self._dev_strs = ivy.default(dev_strs, [self._dev_str])
        self._build_mode = build_mode
        self._stateful = stateful
        self._arg_stateful_idxs = arg_stateful_idxs
        self._kwarg_stateful_idxs = kwarg_stateful_idxs
        self._fallback_to_non_compiled = fallback_to_non_compiled
        self._store_vars = store_vars
        self._built = False
        self._compiled = False
        self._compiled_fn = None
        self._compile_on_next_step = compile_on_next_step
        self._v_in = v
        self.v = v
        self.top_v = None
        self.top_mod = None
        self._sub_mods = set()
        if build_mode != 'on_init':
            return
        self.build()

    # Private #
    # --------#

    def _fn_with_var_arg(self, fn, v_fn):
        def new_fn(*a, with_grads=True, **kw):
            if 'v' in kw.keys():
                del kw['v']
            v = v_fn(self.v)
            if not with_grads:
                v = v.stop_gradients()
            return fn(*a, **kw, v=v)
        new_fn.wrapped = True
        return new_fn

    def _top_v_fn(self, depth=None):
        if ivy.exists(self.top_v):
            if ivy.exists(depth):
                return self.top_v(depth - 1) if depth > 1 else self.v
            return self.top_v()
        return self.v

    def _top_mod_fn(self, depth=None):
        if ivy.exists(self.top_mod):
            if ivy.exists(depth):
                return self.top_mod(depth - 1) if depth > 1 else self
            return self.top_mod()
        return self

    def mod_depth(self):
        depth = 0
        mod_above = self
        while True:
            if ivy.exists(mod_above.top_mod):
                mod_above = mod_above.top_mod(1)
            else:
                break
            depth += 1
        return depth

    def mod_height(self):
        return self.sub_mods().depth - 1

    def _find_variables(self, obj=None):
        vs = Container()
        # ToDo: add support for finding local variables, if/when JAX supports uniquely flagging variables
        if isinstance(obj, Module) and obj is not self:
            obj.top_v = lambda depth=None: self._top_v_fn(depth)
            obj.top_mod = lambda depth=None: self._top_mod_fn(depth)
            self._sub_mods.add(obj)
            return obj.v
        elif isinstance(obj, (list, tuple)):
            for i, v in enumerate(obj):
                ret = self._find_variables(v)
                if ret:
                    vs['v' + str(i)] = ret
            return vs
        elif isinstance(obj, dict):
            for k, v in obj.items():
                ret = self._find_variables(v)
                if ret:
                    vs[k[1:] if k[0] == '_' else k] = ret
            return vs
        elif not hasattr(obj, '__dict__'):
            return vs
        for k, v in obj.__dict__.items():
            if v is not None and k[0:2] != '__':
                ret = self._find_variables(v)
                if ret:
                    vs[k[1:] if k[0] == '_' else k] = ret
        return vs

    @staticmethod
    def _extract_v(v, keychain_mappings, orig_key_chain):
        if v.has_key_chain(orig_key_chain):
            ret_cont = v.at_key_chain(orig_key_chain)
        else:
            ret_cont = ivy.Container()
        for old_kc, new_kc in keychain_mappings.items():
            if orig_key_chain in old_kc:
                ret_cont = ret_cont.set_at_key_chain('/'.join(new_kc.split('/')[1:]), v.at_key_chain(new_kc))
        return ret_cont

    def _wrap_call_methods(self, keychain_mappings, key='', obj=None):
        if isinstance(obj, Module) and obj is not self:
            orig_key_chain = key[1:] if key[0] == '_' else key

            obj.__call__ = self._fn_with_var_arg(obj.__call__,
                                                 lambda v_: self._extract_v(v_, keychain_mappings, orig_key_chain))
            return
        elif isinstance(obj, (list, tuple)):
            for i, val in enumerate(obj):
                self._wrap_call_methods(keychain_mappings, key + '/v' + str(i), val)
            return
        elif isinstance(obj, dict):
            for k, val in obj.items():
                k = (key + '/' + k) if key != '' else k
                self._wrap_call_methods(keychain_mappings, k, val)
            return
        if not hasattr(obj, '__dict__'):
            return
        for k, val in obj.__dict__.items():
            if k[0:2] == '__':
                continue
            k = (key + '/' + k) if key != '' else k
            if val is not None:
                self._wrap_call_methods(keychain_mappings, k, val)
        return

    @staticmethod
    def _remove_duplicate_variables(vs, created):
        created_ids = created.map(lambda x, kc: id(x))
        vs_ids = vs.map(lambda x, kc: id(x))
        ids = dict()
        duplicate_keychains = list()
        keychain_mappings = dict()

        def unique_callback(x, kc):
            ids[x] = kc

        def found_dup_callback(x, kc):
            if ids[x] == kc:
                return
            duplicate_keychains.append(kc)
            keychain_mappings[kc] = ids[x]

        created_ids.map(lambda x, kc: unique_callback(x, kc))
        vs_ids.map(lambda x, kc: unique_callback(x, kc) if x not in ids else found_dup_callback(x, kc))
        for dup_kc in duplicate_keychains:
            vs = vs.prune_key_chain(dup_kc)
        return vs, keychain_mappings

    # Overridable #

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def _create_variables(self, dev_str):
        """
        create internal trainable variables, and return as arbitrary nested dict. Overridable.

        :param dev_str: The device string, specifying the device on which to create the variables.
        :type dev_str: string
        """
        return {}

    def _build(self, *args, **kwargs) -> bool:
        """
        Build the internal layers and variables for this module. Overridable.
        Return False or empty Container if the build only partially completed (i.e. some child Modules have
        "on_call" build mode). Alternatviely, return True or a container of the built variables if the module is built.
        """
        return True

    # Abstract #

    @abc.abstractmethod
    def _forward(self, *args, **kwargs):
        """
        Forward pass of the layer, called after handling the optional input variables.
        """
        raise NotImplementedError

    def _call(self, *args, v=None, with_grads=True, **kwargs):
        """
        the forward pass of the layer, treating layer instance as callable function.
        """
        if not self._built:
            self.build(*args, **kwargs, from_call=True)
        if v is not None:
            v_orig = self.v
            if not with_grads:
                v = v.stop_gradients()
            self.v = Container(v, **v.config) if isinstance(v, Container) else Container(v)
            ret = self._forward(*args, **kwargs)
            self.v = v_orig
            return ret
        elif hasattr(self.__call__, 'wrapped'):
            return self.__call__(*args, with_grads=with_grads, **kwargs)
        elif not with_grads:
            v_orig = self.v
            self.v = v_orig.stop_gradients()
            ret = self._forward(*args, **kwargs)
            self.v = v_orig
            return ret
        return self._forward(*args, **kwargs)

    # Public #
    # -------#

    def sub_mods(self, depth=None):
        if self._sub_mods:
            if ivy.exists(depth):
                if depth == 0:
                    return self.v
                next_depth = depth - 1
            else:
                next_depth = None
            return ivy.Container(
                {str(sm).replace('.', '_').replace('/', '_'): sm.sub_mods(next_depth) for sm in self._sub_mods})
        return self.v

    def show_sub_mods(self, depth=None):
        print(self.sub_mods(depth))

    def show_v_in_top_v(self, depth=None):
        if ivy.exists(self.top_v) and ivy.exists(self.v):
            self.top_v(depth).show_sub_container(self.v)
        else:
            print('both self.top_v and self.v must be initialized in order to show v in top_v,'
                  'but found\n\ntop_v: {}\n\nv: {}.'.format(self.top_v, self.v))

    def compile_graph(self, *args, v=None, with_grads=True, stateful=None, arg_stateful_idxs=None,
                      kwarg_stateful_idxs=None, include_generators=True, **kwargs):
        logging.info('compiling forward pass for network {} ...'.format(self))
        stateful = ivy.default(stateful, self._stateful)
        arg_stateful_idxs = ivy.default(arg_stateful_idxs, self._arg_stateful_idxs)
        kwarg_stateful_idxs = ivy.default(kwarg_stateful_idxs, self._kwarg_stateful_idxs)
        stateful = ivy.default(stateful, self._stateful)
        if not self._built:
            if self._build_mode == 'on_call':
                self(*args, v=v, with_grads=with_grads, **kwargs)
            elif self._build_mode == 'explicit':
                self.build(*args, from_call=False, **kwargs)
            elif self._build_mode == 'on_init':
                raise Exception('ivy.Module constructor was called but module was not built despite '
                                'on_init mode being set.')
            else:
                raise Exception('invalid build_mode, must be one of [ on_call | explicit | on_init ]')
        kwargs['v'] = ivy.default(v, self.v)
        kwargs['with_grads'] = with_grads
        self._compiled_fn = ivy.compile_graph(
            self._call, *args, **kwargs, stateful=stateful, arg_stateful_idxs=arg_stateful_idxs,
            kwarg_stateful_idxs=kwarg_stateful_idxs, include_generators=include_generators, name=str(self))
        logging.info('{} forward pass compiled!'.format(self))
        self._compiled = True

    def show_graph(self, *args, v=None, with_grads=True, stateful=None, arg_stateful_idxs=None,
                   kwarg_stateful_idxs=None, randomness_factor=0., save_to_disk=False, with_edge_labels=True,
                   with_arg_labels=True, with_output_labels=True, output_connected_only=True, include_generators=True,
                   fname=None, **kwargs):
        self(*args, v=v, with_grads=with_grads, **kwargs)  # for on call build modes
        if not self._built:
            self.build(*args, from_call=False, **kwargs)  # for explicit build modes
        kwargs['v'] = ivy.default(v, self.v)
        kwargs['with_grads'] = with_grads
        ivy.show_graph(self._call, *args, **kwargs, stateful=stateful, arg_stateful_idxs=arg_stateful_idxs,
                       kwarg_stateful_idxs=kwarg_stateful_idxs, randomness_factor=randomness_factor,
                       save_to_disk=save_to_disk, with_edge_labels=with_edge_labels, with_arg_labels=with_arg_labels,
                       with_output_labels=with_output_labels, output_connected_only=output_connected_only,
                       include_generators=include_generators, fname=fname, name=str(self))

    def compile_on_next_step(self):
        self._compile_on_next_step = True

    def __call__(self, *args, v=None, with_grads=True, stateful=None, arg_stateful_idxs=None, kwarg_stateful_idxs=None,
                 **kwargs):
        if self._compiled and ivy.try_use_compiled:
            try:
                return self._compiled_fn(*args, v=ivy.default(v, self.v), with_grads=with_grads, **kwargs)
            except Exception as e:
                if self._fallback_to_non_compiled:
                    return self._call(*args, v=v, with_grads=with_grads, **kwargs)
                raise e
        elif self._compile_on_next_step and not self._compiled:
            self.compile_graph(*args, v=v, with_grads=with_grads, stateful=stateful,
                               arg_stateful_idxs=arg_stateful_idxs, kwarg_stateful_idxs=kwarg_stateful_idxs, **kwargs)
            self._compile_on_next_step = False
            return self._compiled_fn(*args, v=ivy.default(v, self.v), with_grads=with_grads, **kwargs)
        return self._call(*args, v=v, with_grads=with_grads, **kwargs)

    def save_weights(self, weights_path):
        """
        Save the weights on the Module.
        :param weights_path: The hdf5 file for saving the weights.
        :type weights_path: string
        """
        os.makedirs('/'.join(weights_path.split('/')[:-1]), exist_ok=True)
        self.v.to_disk_as_hdf5(weights_path)

    def build(self, *args, from_call=False, dev_str=None, **kwargs):
        """
        Build the internal layers and variables for this module.
        """
        self._dev_str = ivy.default(dev_str, self._dev_str)

        # return False if not from_call but build_mode is on_call
        if not from_call and self._build_mode == 'on_call':
            return self.v

        # build local Module, and any child modules flagged with "explicit" build mode
        built = ivy.default(self._build(*args, **kwargs), True)

        # build variables based on locally built layers, if v not passed in constructor
        v_from_constructor = self._v_in
        created = Container()
        if not ivy.exists(v_from_constructor):
            created = Container(self._create_variables(self._dev_str))
            vs = Container(dict(**self._find_variables(self), **created))
            self.v = vs
        elif not isinstance(self.v, Container):
            self.v = Container(self.v)

        # remove duplicates
        self.v, keychain_mappings = self._remove_duplicate_variables(self.v, created)

        # build any child 'on_call' layers
        if not built and from_call:

            # update child modules to share the same device
            for k, v in self.__dict__.items():
                if isinstance(v, ivy.Module):
                    v._dev_str = self._dev_str

            # build during forward pass
            self._forward(*args, **kwargs)

            # re-build variables based on additional child on-call layers, if v not passed in constructor
            if not ivy.exists(v_from_constructor):
                vs = Container(dict(**self._find_variables(self), **self._create_variables(self._dev_str)))
                self.v = vs

            # remove further duplicates with self.v
            self.v, keychain_mappings = self._remove_duplicate_variables(self.v, created)

            # set built flag
            built = True

        # wrap call methods if the module is fully built
        if built:
            self._wrap_call_methods(keychain_mappings, obj=self)

        # flag built and remove local variables if specified
        self._built = bool(built)
        v_ret = self.v
        if not self._store_vars:
            # ToDo: verify variables in self.v are released once this method exits
            self.v = ivy.Container()
        return v_ret if bool(v_ret) or isinstance(built, bool) else built

    # Properties #
    # -----------#

    @property
    def build_mode(self):
        return self._build_mode

    @property
    def built(self):
        return self._built
