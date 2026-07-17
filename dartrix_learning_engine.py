import numpy as np
import tensorflow as tf
from scipy.optimize import differential_evolution
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, Matern
import optuna

class SelfLearningDARTRIX:
    """
    Samouczący się model DARTRIX – łączy równanie spinarno-binarne
    z uczeniem maszynowym i optymalizacją meta-parametrów.
    """
    
    def __init__(self):
        self.R2 = 1007
        self.K = 1848181
        self.b = 1/999
        self.theta_multiplier = 11
        self.learning_rate = 0.001
        self.episodes = 1000
        self.state_dim = 4
        self.action_dim = 3
        self.gp_model = None
        self.rl_agent = None
        self.meta_optimizer = None
        self.experience_buffer = []
        self.max_buffer_size = 10000
        self.performance_history = []
        self.parameter_history = []
        self._initialize_models()
    
    def _initialize_models(self):
        kernel = 1.0 * RBF(length_scale=1.0) + WhiteKernel(noise_level=0.1)
        self.gp_model = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10, alpha=1e-6, normalize_y=True)
        self.rl_agent = self._build_rl_agent()
        self.meta_optimizer = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
    
    def _build_rl_agent(self):
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(self.state_dim,)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(self.action_dim, activation='tanh')
        ])
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate), loss='mse')
        return model
    
    def q(self, t):
        return 1.0 if np.sin(t) > 0 else 0.0
    
    def theta(self, t):
        return self.theta_multiplier * t
    
    def dNdt(self, N, t, R2=None, K=None, b=None):
        R2 = R2 or self.R2
        K = K or self.K
        b = b or self.b
        q_val = self.q(t)
        theta_val = self.theta(t)
        return (R2 ** q_val) * np.exp(b * theta_val) * (1 - N / K)
    
    def simulate(self, t_max=10, steps=1000, params=None):
        if params:
            R2, K, b = params
        else:
            R2, K, b = self.R2, self.K, self.b
        t = np.linspace(0, t_max, steps)
        N = np.zeros_like(t)
        N[0] = 1.0
        for i in range(1, len(t)):
            dt = t[i] - t[i-1]
            N[i] = N[i-1] + self.dNdt(N[i-1], t[i-1], R2, K, b) * dt
        return t, N
    
    def fit_gp_model(self, X_train, y_train):
        self.gp_model.fit(X_train, y_train)
        return self.gp_model
    
    def predict_with_gp(self, X_test):
        return self.gp_model.predict(X_test, return_std=True)
    
    def collect_experience(self, state, action, reward, next_state, done):
        self.experience_buffer.append({'state': state, 'action': action, 'reward': reward, 'next_state': next_state, 'done': done})
        if len(self.experience_buffer) > self.max_buffer_size:
            self.experience_buffer.pop(0)
    
    def learn_from_experience(self, batch_size=64):
        if len(self.experience_buffer) < batch_size: return
        indices = np.random.choice(len(self.experience_buffer), batch_size, replace=False)
        batch = [self.experience_buffer[i] for i in indices]
        states = np.array([exp['state'] for exp in batch])
        actions = np.array([exp['action'] for exp in batch])
        rewards = np.array([exp['reward'] for exp in batch])
        next_states = np.array([exp['next_state'] for exp in batch])
        dones = np.array([exp['done'] for exp in batch])
        target_q = rewards + 0.99 * (1 - dones) * self.rl_agent.predict(next_states).max(axis=1)
        self.rl_agent.fit(states, target_q, epochs=1, verbose=0)
    
    def get_action(self, state, explore=True):
        state = np.array(state).reshape(1, -1)
        if explore and np.random.random() < 0.3:
            return np.random.uniform(-0.1, 0.1, self.action_dim)
        else:
            return self.rl_agent.predict(state)[0]
    
    def objective_function(self, params):
        R2, K, b = params
        try:
            t, N = self.simulate(params=(R2, K, b))
            final_N = N[-1]
            penalty = 1000 * (final_N - K * 0.95) ** 2 if final_N > K * 0.95 else 0
            return final_N - penalty
        except Exception: return -1e6
    
    def optimize_parameters(self, n_trials=100):
        def objective(trial):
            R2 = trial.suggest_int('R2', 900, 1200)
            K = trial.suggest_int('K', 500000, 3000000)
            b = trial.suggest_float('b', 0.0001, 0.01)
            return self.objective_function([R2, K, b])
        self.meta_optimizer.optimize(objective, n_trials=n_trials)
        best_params = self.meta_optimizer.best_params
        self.R2 = best_params['R2']
        self.K = best_params['K']
        self.b = best_params['b']
        return best_params
    
    def self_develop(self, target_data=None, n_episodes=1000):
        for episode in range(n_episodes):
            t = np.random.uniform(0, 10)
            N = np.random.uniform(1, self.K * 0.1)
            q_val = self.q(t)
            theta_val = self.theta(t)
            state = np.array([N, t, q_val, theta_val])
            action = self.get_action(state)
            delta_R2, delta_K, delta_b = action
            new_R2 = max(900, min(1200, self.R2 + delta_R2 * 100))
            new_K = max(500000, min(3000000, self.K + delta_K * 100000))
            new_b = max(0.0001, min(0.01, self.b + delta_b * 0.001))
            t_sim, N_sim = self.simulate(params=(new_R2, new_K, new_b))
            new_N = N_sim[-1]
            if target_data is not None:
                target_N = np.interp(t_sim, target_data['t'], target_data['N'])
                reward = -np.mean((N_sim - target_N) ** 2)
            else:
                growth_rate = (N_sim[-1] - N_sim[0]) / N_sim[0]
                reward = growth_rate * (1.0 if N_sim[-1] < self.K * 0.95 else 0.0)
            new_state = np.array([new_N, t_sim[-1], self.q(t_sim[-1]), self.theta(t_sim[-1])])
            done = t_sim[-1] >= 10
            self.collect_experience(state, action, reward, new_state, done)
            if len(self.experience_buffer) >= 64: self.learn_from_experience()
            if reward > 0:
                self.R2 = new_R2
                self.K = new_K
                self.b = new_b
            self.performance_history.append({'episode': episode, 'reward': reward, 'R2': self.R2, 'K': self.K, 'b': self.b, 'N_final': new_N})
            if episode % 100 == 0 and episode > 0: self.optimize_parameters(n_trials=20)
        return self.performance_history
    
    def auto_build(self, complexity_level='medium'):
        levels = {'simple': {'agents': ['sensor', 'analysis'], 'features': ['N', 't', 'q'], 'memory_size': 1000},
                  'medium': {'agents': ['sensor', 'analysis', 'decision', 'intervention'], 'features': ['N', 't', 'q', 'theta', 'gradient'], 'memory_size': 5000},
                  'complex': {'agents': ['sensor', 'analysis', 'decision', 'intervention', 'learning', 'meta'], 'features': ['N', 't', 'q', 'theta', 'gradient', 'second_derivative', 'entropy'], 'memory_size': 10000}}
        config = levels.get(complexity_level, levels['medium'])
        self.state_dim = len(config['features'])
        self.max_buffer_size = config['memory_size']
        self.rl_agent = self._build_advanced_rl_agent(len(config['features']))
        return config
    
    def _build_advanced_rl_agent(self, input_dim):
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu', input_shape=(input_dim,)),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(self.action_dim, activation='tanh')
        ])
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0005), loss='huber')
        return model

if __name__ == "__main__":
    system = SelfLearningDARTRIX()
    system.auto_build(complexity_level='medium')
    system.self_develop(n_episodes=1000)
    print(system.generate_report())
