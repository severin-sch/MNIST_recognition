import numpy as np
from activations import *

class Network:
    """Network class that stores layers, and organises interactions between them
    
    Parameters:
    -----------
    learning_rate:
                float
                Learning rate for network, used during backpropagation. Should be between 0 and 1.
    *layers:    keyword arguments used to construct layers
                Assuming first layer is of type Input, last of type Output, and the one(s) in between Dense.
    """
    def __init__(self, layers=[], name="Neural", momentum=0, learning_rate=0.006):
        self.name = name
        self.learning_rate = learning_rate if callable(learning_rate) else lambda step: learning_rate
        self.network = []
        self.momentum = momentum

        for i, layer in enumerate(layers):
            if i == 0:
                self.addLayer(Input(**layer))
            elif i == len(layers) - 1:
                self.addLayer(Output(**layer))
                self.compile()
            else:
                self.addLayer(Dense(**layer))

    @property
    def property_dict(self):
        properties = {'model_name': self.name,
                      'momentum': self.momentum,
                      'learning_rate': self.learning_rate_name,
                      'layers': ', '.join([str(layer.height) for layer in self.network])
                      }
        return properties

    @property
    def learning_rate_name(self):
        if callable(self.learning_rate):
            if self.learning_rate.__doc__ is not None:
                return self.learning_rate.__doc__
            else:
                return f"(0) {self.learning_rate(0)}"
        else:
            return f"flat {self.learning_rate}"

    @property
    def parallell_runs(self):
        return 1 #self.network[-1].height

    def addLayer(self, layer):
        """Add a layer to network.
        
        Parameters:
        -----------
        layer:      subclass of Layer
                    Layer to add to the end of this network.
        """
        self.network.append(layer)

    def compile(self, x1=None, x2=None, momentum=None):
        """Compiles the network by initialising weights, and making the list of layers an array.

        Also functions as a reset to random initial conditions.
        """
        self.step = 0
        for i in range(1, len(self.network)):
            self.network[i].set_prevLayer(self.network[i-1].height)
        self.network = np.asarray(self.network)

    def feed_forward(self, input_neurons):
        """Feeds forward through the network with a given input.
        
        Parameters:
        -----------
        input_neurons:
                    array of floats
                    Input values. Must have same shape as input layer.
        """
        self.network[0].a = input_neurons

        for i in range(1, len(self.network)):
            self.network[i].feed_forward(self.network[i-1])

    def predict(self, x):
        """ Predicts on x

        Parameters:
        -----------
        x:          array of floats

        Returns:
        prediction: array of prediction(s)
        """
        self.feed_forward(x)
        return self.network[-1].a

    def class_predict(self, x):
         pred = self.predict(x)
         return np.argmax(pred, axis=1)

    def update_parameters(self, x, optimal_output, ytilde):
        """Propagates the error back through the network, and steps in a direction of less loss.
        
        Parameters:
        -----------
        x:          for compatibility with sgd
        optimal_output:
                    array of floats
                    Optimal or desired output values. Must have same shape as output layer.
        y:          for compatibility with sgd
        """

        for i in reversed(range(1, len(self.network))):
            if i == len(self.network) - 1:
                backprop_data = optimal_output
            else:
                backprop_data = self.network[i+1]

            self.network[i].back_propagate(backprop_data)

            self.network[i].bias_velocity *= self.momentum
            self.network[i].bias_velocity += self.learning_rate(self.step) * np.mean(self.network[i].d, axis=0)
            self.network[i].bias += self.network[i].bias_velocity
            self.network[i].bias_history.append((np.mean(self.network[i].bias), np.std(self.network[i].bias)))

            #print(i, '\n', self.network[i].bias, '\n', self.network[i].weights)

            self.network[i].weights_velocity *= self.momentum
            self.network[i].weights_velocity += self.learning_rate(self.step) * 1/self.network[i-1].height * np.dot(self.network[i - 1].a.T, self.network[i].d)
            self.network[i].weights += self.network[i].weights_velocity
            self.network[i].weights_history.append((np.mean(self.network[i].weights), np.std(self.network[i].weights)))

        self.step += 1

    def __str__(self):
        """Returns a printable string with all the networks biases and weights.
        """
        string = "Neural net\n"
        for i in range(1, len(self.network)):
            string += f"Layer {i}\n   Biases: {self.network[i].bias.shape}\n   Weights: {self.network[i].weights.shape}\n"
            #string += f"delta_b = {self.network[i].delta_b.shape}\n delta_w: {self.network[i].delta_w.shape}"
        return string

    def plot_history(self):
        """Plots history of mean and std of weights and biases over steps"""
        import matplotlib.pyplot as plt
        import plotting

        x = np.arange(self.step)
        fig, ax = plt.subplots(figsize=(7,7))

        weights, bias = np.zeros((2, 3, self.step))
        for i, layer in enumerate(self.network[1:]):
            weights_mean = np.array([mean for mean, _ in layer.weights_history])
            weights_std = np.array([std for _, std in layer.weights_history])

            weights[0] = weights_mean - weights_std
            weights[1] = weights_mean
            weights[2] = weights_mean + weights_std

            plotting.confidence_interval_plotter(ax, x, weights, color=f"C{2*i+1}", alpha=0.1)

            bias_mean = np.array([mean for mean, _ in layer.bias_history])
            bias_std = np.array([std for _, std in layer.bias_history])
            
            bias[0] = bias_mean - bias_std
            bias[1] = bias_mean
            bias[2] = bias_mean + bias_std

            plotting.confidence_interval_plotter(ax, x, bias, color=f"C{2*i}", alpha=0.1)

        plt.title(f"Weights and biases of {self.name.lower()} over training")
        plt.xlabel("Steps")
        plt.ylabel("Parameter values")

        label_enum = np.arange((len(self.network) - 1)*2)
        colors = [f"C{number}" for number in label_enum]
        handler_map = {i: plotting.LegendObject(colors[i]) for i in range(len(colors))}
        labels = [f"{p_type}, layer {i}" for i in range(1, len(self.network)) for p_type in ['Bias', 'Weights']]
        ax.legend(label_enum, labels, handler_map=handler_map)
        
        plt.savefig(f"../plots/{self.name}_bias_weights_history.png")

def MSE_diff(actualOutput, optimal_output):
    return 2 * (optimal_output - actualOutput)

class Layer:
    """Generic layer in neural network.

    Parameters:
    -----------
    height:     int
                Number of neurons in layer.
    """
    def __init__(self, height):
        self.a = np.zeros(height)
        self.height = height


class Input(Layer):
    """Input layer in neural network.

    Parameters:
    -----------
    height:     int
                Number of neurons in layer.
    """
    def __init__(self, height):
        super().__init__(height)


class Dense(Layer):
    """Hidden, dense layer in neural network.

    Parameters:
    -----------
    height:     int
                Number of neurons in layer.
    activation: array of floats -> array of floats
                Activation function. Sigmoid by default.
    diff_activation:
                array of floats -> array of floats
                Differentiation of activation function.
    """
    def __init__(self, height, activations=sigmoids):
        super().__init__(height)
        self.z = np.zeros_like(self.a)
        self.d = np.zeros_like(self.a)
        self.activation, self.diff_activation = activations

    def feed_forward(self, prevLayer):
        """Feed forward values through this layer.

        Parameters:
        -----------
        prevLayer:  array of floats
                    Activation values from previous layer
        """

        self.z = np.dot(prevLayer.a, self.weights) + self.bias

        self.a = self.activation(self.z)

    def back_propagate(self, nextLayer):
        self.d = np.dot(nextLayer.weights, nextLayer.d.T).T * self.diff_activation(self.z)

    def set_prevLayer(self, prevLayerHeight):
        """Initialise weights and biases after making the layer before it.

        Parameters:
        -----------
        prevLayerHeight:
                    int
                    Number of neurons in previous layer.
        """
        self.weights = np.random.normal(0, 1/self.height, (prevLayerHeight, self.height))
        self.bias = np.zeros(self.height)

        self.weights_velocity = np.zeros_like(self.weights)
        self.bias_velocity = np.zeros_like(self.bias)

        self.weights_history = []
        self.bias_history = [] 

class Output(Dense):
    """Output layer for neural network.

    Parameters:
    -----------
    height:     int
                Number of neurons in layer.
    activation: array of floats -> array of floats
                Activation function. Sigmoid by default.
    diff_activation:
                array of floats -> array of floats
                Differentiation of activation function.
    cost_diff:  array of floats -> array of floats
                Differentiation of cost function.
    d_func:     (a, y, z) -> cost
                Cost function, wih regards to z. Overwrites diff_activation and cost_diff.
    """
    def __init__(self, height, activations=sigmoids, cost_diff=MSE_diff, d_func=None):
        if d_func is None:
            super().__init__(height, activations=activations)
            self.cost_diff = cost_diff
            self.d_func = lambda a, y, z: self.cost_diff(a, y) * self.diff_activation(z)
        else:
            super().__init__(height, activations=activations)
            self.cost_diff = None
            self.d_func = d_func

    def back_propagate(self, y):
        """back_propagate error through this layer.

        Parameters:
        -----------
        y:          array of floats
                    Optimal output.
        """
        self.d = self.d_func(self.a, y, self.z)

if __name__ == "__main__":
    import plotting
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(5, 5))
    plotting.draw_neural_net(fig.gca(), .1, .9, .1, .9, [3, 4, 4, 3],
                             [[r'$x_1$', '...', r'$x_M$'], [], [], [r"$y_1$", "...", r"$y_K$"]])
    plt.tight_layout()
    plt.show()