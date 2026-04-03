import random
import copy
import numpy as np
from model.simulator import Simulation
from stats.analyze import SimulationAnalyzer
from stats.sensitivity_analyzer import SensitivityAnalyzer

class SimulationOptimizer:
    def __init__(self, base_config, evaluator):
        self.base_config = base_config
        self.evaluator = evaluator
        self.history = []
        self.plotter = SensitivityAnalyzer(base_config)

    def _generate_random_config(self):
        new_config = copy.deepcopy(self.base_config)
        new_config['video_bitrate'] = random.randint(2501, 6999)
        new_config['gop_size'] = random.randint(51, 299)
        new_config['bandwidth'] = random.randint(3001, 7499)
        new_config['jitter_intensity'] = round(random.uniform(0.0011, 0.0499), 4)
        new_config['packet_loss_probability'] = round(random.uniform(0.0001, 0.0499), 4)
        return new_config

    def run_random_search(self, num_combinations=50, runs_per_combination=5, sim_duration=3000):
        print(f"\tЗапуск оптимизации (Random Search: {num_combinations} комбинаций) ")
        best_config, best_qoe = None, float('-inf')
        valid_tested = 0
        
        while valid_tested < num_combinations:
            config = self._generate_random_config()
            if not self.evaluator.check_constraints(config):
                continue
                
            analyzer = SimulationAnalyzer()
            valid_tested += 1
            print(f"[{valid_tested}/{num_combinations}] Тест: V={config['video_bitrate']}, B={config['bandwidth']}, G={config['gop_size']}, J={config['jitter_intensity']:.4f}, P={config['packet_loss_probability']:.3f}")

            for _ in range(runs_per_combination):
                config['random_seed'] = random.randint(1, 100000)
                sim = Simulation(config)
                sim.run(sim_duration)
                analyzer.save_run(sim.stats)
            
            avg_stall, avg_sync = analyzer.get_average_metrics()
            qoe_score = self.evaluator.calculate(config['video_bitrate'], avg_stall, avg_sync)
            
            entry = {'config': config, 'avg__total_stall': avg_stall, 'avg__total_sync': avg_sync, 'qoe': qoe_score}
            self.history.append(entry)
            
            if qoe_score > best_qoe:
                best_qoe = qoe_score
                best_config = entry

        return self.history, best_config

    def run_isolated_analysis(self, param_ranges, runs_per_point=3, sim_duration=2500):
        print("\n\tЗапуск изолированного анализа...")
        results = {}
        
        center_config = copy.deepcopy(self.base_config)

        for param, values in param_ranges.items():
            print(f"Изолированное исследование: {param}")
            param_results = []
            
            for val in values:
                cfg = copy.deepcopy(center_config)
                cfg[param] = val

                if not self.evaluator.check_constraints(cfg):
                    print(f"  Пропуск {param}={val} из-за нарушения ограничений.")
                    continue
                    
                analyzer = SimulationAnalyzer()
                for _ in range(runs_per_point):
                    cfg['random_seed'] = random.randint(1, 100000)
                    sim = Simulation(cfg)
                    sim.run(sim_duration)
                    analyzer.save_run(sim.stats)
                
                avg_stall, avg_sync = analyzer.get_average_metrics()
                qoe = self.evaluator.calculate(cfg['video_bitrate'], avg_stall, avg_sync)
                param_results.append((val, qoe))
            
            results[param] = param_results
            self.plotter.plot_isolated_dependencies(results, param_name=param)

        return results