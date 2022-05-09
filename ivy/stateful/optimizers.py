"""Collection of Ivy optimizers."""

# global
import abc

# local
import ivy


# Base #
# -----#


class Optimizer(abc.ABC):
    def __init__(
        self,
        lr,
        inplace=None,
        stop_gradients=True,
        init_on_first_step=False,
        compile_on_next_step=False,
        fallback_to_non_compiled=False,
        device=None,
    ):
        """Construct an general Optimizer. This is an abstract class, and must be
        derived.

        :param lr: Learning rate.
        :type lr: function or float.
        :param inplace: Whether to update the variables in-place, or to create new
                        variable handles. This is only relevant for frameworks with
                        stateful variables such as PyTorch. Default is True, provided
                        the backend framework supports it.
        :type inplace: bool, optional
        :param stop_gradients: Whether to stop the gradients of the variables after each
                               gradient step. Default is True.
        :type stop_gradients: bool, optional
        :param init_on_first_step: Whether the optimizer is initialized on the first
                                   step. Default is False.
        :type init_on_first_step: bool, optional
        :param compile_on_next_step: Whether to compile the optimizer on the next step.
                                     Default is False.
        :type compile_on_next_step: bool, optional
        :param fallback_to_non_compiled: Whether to fall back to non-compiled forward
                                         call in the case that an error is raised during
                                         the compiled forward pass. Default is True.
        :type fallback_to_non_compiled: bool, optional
        :param device: device on which to create the layer's variables 'cuda:0',
                       'cuda:1', 'cpu' etc.
        :type device: ivy.Device, optional

        """
        self._lr = lr
        self._inplace = inplace
        self._stop_gradients = stop_gradients
        self._init_on_first_step = init_on_first_step
        self._initialized = not init_on_first_step
        self._compile_on_next_step = compile_on_next_step
        self._fallback_to_non_compiled = fallback_to_non_compiled
        self._dev = ivy.default(device, ivy.default_device())
        self._count = ivy.array([0], device=self._dev)
        self._compiled_step_fn = None
        self._compiled = False

    # Private #
    # --------#

    # Abstract #

    @abc.abstractmethod
    def _step(self, v, grads):
        """Update nested variables container v from update step, using nested grads
        container. Override this abstract method with child class custom implementation.

        :param v: Nested variables to update.
        :type v: Ivy container of variables
        :param grads: Nested gradients to update.
        :type grads: sequence of arrays
        :return: The updated variables, following update step.

        """
        raise NotImplementedError

    # Given #

    def _step_fn(self, v, grads, ignore_missing):
        if ignore_missing:
            return v.set_at_keys(self._step(v.at_key_chains(grads), grads))
        return self._step(v, grads)

    # Public #
    # -------#

    # Abstract #

    @abc.abstractmethod
    def set_state(self, state):
        """Set state of the optimizer.

        :param state: Nested state to update.
        :type state: Ivy container of state tensors

        """
        raise NotImplementedError

    # Given #

    def step(self, v, grads, ignore_missing=False):
        """Update nested variables container v from overriden private self._step.

        :param v: Nested variables to update.
        :type v: Ivy container of variables
        :param grads: Nested gradients to update.
        :type grads: sequence of arrays
        :param ignore_missing: Whether to ignore keys missing from the gradients which exist in the variables.
                               Default is False.
        :type ignore_missing: bool, optional
        :return: The updated variables, following update step.

        """
        self._count += 1
        self._initialized = True
        return self._step_fn(v, grads, ignore_missing)


# Optimizers #
# -----------#


class SGD(Optimizer):
    def __init__(
        self,
        lr=lambda: 1e-4,
        inplace=None,
        stop_gradients=True,
        compile_on_next_step=False,
    ):
        """Construct a Stochastic-Gradient-Descent (SGD) optimizer.

        :param lr: Learning rate, default is 1e-4.
        :type lr: float, optional
        :param inplace: Whether to update the variables in-place, or to create new
                        variable handles. This is only relevant for frameworks with
                        stateful variables such as PyTorch. Default is True, provided
                        the backend framework supports it.
        :type inplace: bool, optional
        :param stop_gradients: Whether to stop the gradients of the variables after each
                               gradient step. Default is True.
        :type stop_gradients: bool, optional
        :param compile_on_next_step: Whether to compile the optimizer on the next step.
                                     Default is False.
        :type compile_on_next_step: bool, optional

        """
        Optimizer.__init__(
            self, lr, inplace, stop_gradients, compile_on_next_step=compile_on_next_step
        )

    # Custom Step

    def _step(self, v, grads):
        """Update nested variables container v by gradient descent step, using nested
        gradients container.

        :param v: Nested variables to update.
        :type v: Ivy container of variables
        :param grads: Nested gradients to update.
        :type grads: sequence of arrays
        :return: The new updated variables container, following gradient descent step.

        """
        return ivy.gradient_descent_update(
            v,
            grads,
            self._lr if isinstance(self._lr, float) else self._lr(),
            self._inplace,
            self._stop_gradients,
        )

    def set_state(self, state):
        """Set state of the optimizer.

        :param state: Nested state to update.
        :type state: Ivy container of state tensors

        """
        pass

    @property
    def state(self):
        return ivy.Container({})


class LARS(Optimizer):
    def __init__(
        self,
        lr=lambda: 1e-4,
        decay_lambda=0,
        inplace=None,
        stop_gradients=True,
        compile_on_next_step=False,
    ):
        """Construct a Layerwise Adaptive Rate Scaling (LARS) optimizer.

        :param lr: Learning rate, default is 1e-4.
        :type lr: float, optional
        :param decay_lambda: The factor used for weight decay. Default is zero.
        :type decay_lambda: float, optional
        :param inplace: Whether to update the variables in-place, or to create new
                        variable handles. This is only relevant for frameworks with
                        stateful variables such as PyTorch. Default is True, provided
                        the backend framework supports it.
        :type inplace: bool, optional
        :param stop_gradients: Whether to stop the gradients of the variables after each
                               gradient step. Default is True.
        :type stop_gradients: bool, optional
        :param compile_on_next_step: Whether to compile the optimizer on the next step.
                                     Default is False.
        :type compile_on_next_step: bool, optional

        """
        self._decay_lambda = decay_lambda
        Optimizer.__init__(
            self, lr, inplace, stop_gradients, compile_on_next_step=compile_on_next_step
        )

    # Custom Step

    def _step(self, v, grads):
        """Update nested variables container v by gradient descent step, using nested
        gradients container.

        :param v: Nested variables to update.
        :type v: Ivy container of variables
        :param grads: Nested gradients to update.
        :type grads: sequence of arrays
        :return: The new updated variables container, following LARS step.

        """
        return ivy.lars_update(
            v,
            grads,
            self._lr if isinstance(self._lr, float) else self._lr(),
            self._decay_lambda,
            self._inplace,
            self._stop_gradients,
        )

    def set_state(self, state):
        """Set state of the optimizer.

        :param state: Nested state to update.
        :type state: Ivy container of state tensors

        """
        pass

    @property
    def state(self):
        return ivy.Container({})


class Adam(Optimizer):
    def __init__(
        self,
        lr=1e-4,
        beta1=0.9,
        beta2=0.999,
        epsilon=1e-07,
        inplace=None,
        stop_gradients=True,
        compile_on_next_step=False,
        device=None,
    ):
        """Construct an ADAM optimizer.

        :param lr: Learning rate, default is 1e-4.
        :type lr: float, optional
        :param beta1: gradient forgetting factor, default is 0.9
        :type beta1: float, optional
        :param beta2: second moment of gradient forgetting factor, default is 0.999
        :type beta2: float, optional
        :param epsilon: divisor during adam update, preventing division by zero, default
                        is 1e-07
        :type epsilon: float, optional
        :param inplace: Whether to update the variables in-place, or to create new
                        variable handles. This is only relevant for frameworks with
                        stateful variables such as PyTorch. Default is True, provided
                        the backend framework supports it.
        :type inplace: bool, optional
        :param stop_gradients: Whether to stop the gradients of the variables after each
                               gradient step. Default is True.
        :type stop_gradients: bool, optional
        :param compile_on_next_step: Whether to compile the optimizer on the next step.
                                     Default is False.
        :type compile_on_next_step: bool, optional
        :param device: device on which to create the layer's variables 'cuda:0',
                       'cuda:1', 'cpu' etc.
        :type device: ivy.Device, optional

        """
        Optimizer.__init__(
            self, lr, inplace, stop_gradients, True, compile_on_next_step, device
        )
        self._beta1 = beta1
        self._beta2 = beta2
        self._epsilon = epsilon
        self._mw = None
        self._vw = None
        self._first_pass = True
        self._should_compile = False

    # Custom Step

    def _step(self, v, grads):
        """Update nested variables container v by Adam update step, using nested grads
        container.

        :param v: Nested variables to update.
        :type v: Ivy container of variables
        :param grads: Nested gradients to update.
        :type grads: sequence of arrays
        :return: The updated variables, following Adam update step.

        """
        if self._first_pass:
            self._mw = grads
            self._vw = grads**2
            self._first_pass = False
        new_v, self._mw, self._vw = ivy.adam_update(
            v,
            grads,
            self._lr if isinstance(self._lr, float) else self._lr(),
            self._mw,
            self._vw,
            self._count,
            self._beta1,
            self._beta2,
            self._epsilon,
            self._inplace,
            self._stop_gradients,
        )
        return new_v

    def set_state(self, state):
        """Set state of the optimizer.

        :param state: Nested state to update.
        :type state: Ivy container of state tensors

        """
        self._mw = state.mw
        self._vw = state.vw

    @property
    def state(self):
        return ivy.Container({"mw": self._mw, "vw": self._vw})


class LAMB(Optimizer):
    def __init__(
        self,
        lr=1e-4,
        beta1=0.9,
        beta2=0.999,
        epsilon=1e-07,
        max_trust_ratio=10,
        decay_lambda=0,
        inplace=None,
        stop_gradients=True,
        compile_on_next_step=False,
        device=None,
    ):
        """Construct an LAMB optimizer.

        :param lr: Learning rate, default is 1e-4.
        :type lr: float, optional
        :param beta1: gradient forgetting factor, default is 0.9
        :type beta1: float, optional
        :param beta2: second moment of gradient forgetting factor, default is 0.999
        :type beta2: float, optional
        :param epsilon: divisor during adam update, preventing division by zero, default
                        is 1e-07
        :type epsilon: float, optional
        :param max_trust_ratio: The max value of the trust ratio; the ratio between the
                                norm of the layer weights and norm of gradients update.
                                Default is 10.
        :type max_trust_ratio: float, optional
        :param decay_lambda: The factor used for weight decay. Default is zero.
        :type decay_lambda: float, optional
        :param inplace: Whether to update the variables in-place, or to create new
                        variable handles. This is only relevant for frameworks with
                        stateful variables such as PyTorch. Default is True, provided
                        the backend framework supports it.
        :type inplace: bool, optional
        :param stop_gradients: Whether to stop the gradients of the variables after each
                               gradient step. Default is True.
        :type stop_gradients: bool, optional
        :param compile_on_next_step: Whether to compile the optimizer on the next step.
                                     Default is False.
        :type compile_on_next_step: bool, optional
        :param device: device on which to create the layer's variables 'cuda:0',
                       'cuda:1', 'cpu' etc.
        :type device: ivy.Device, optional

        """
        Optimizer.__init__(
            self, lr, inplace, stop_gradients, True, compile_on_next_step, device
        )
        self._beta1 = beta1
        self._beta2 = beta2
        self._epsilon = epsilon
        self._mw = None
        self._vw = None
        self._max_trust_ratio = max_trust_ratio
        self._decay_lambda = decay_lambda
        self._first_pass = True

    # Custom Step

    def _step(self, v, grads):
        """Update nested variables container v by LAMB update step, using nested grads
        container.

        :param v: Nested variables to update.
        :type v: Ivy container of variables
        :param grads: Nested gradients to update.
        :type grads: sequence of arrays
        :return: The updated variables, following LAMB update step.

        """
        if self._first_pass:
            self._mw = grads
            self._vw = grads**2
            self._first_pass = False
        new_v, self._mw, self._vw = ivy.lamb_update(
            v,
            grads,
            self._lr if isinstance(self._lr, float) else self._lr(),
            self._mw,
            self._vw,
            self._count,
            self._beta1,
            self._beta2,
            self._epsilon,
            self._max_trust_ratio,
            self._decay_lambda,
            self._inplace,
            self._stop_gradients,
        )
        return new_v

    def set_state(self, state):
        """Set state of the optimizer.

        :param state: Nested state to update.
        :type state: Ivy container of state tensors

        """
        self._mw = state.mw
        self._vw = state.vw

    @property
    def state(self):
        return ivy.Container({"mw": self._mw, "vw": self._vw})
