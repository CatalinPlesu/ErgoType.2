using System;
using System.Collections.Generic;
using System.Linq;

namespace KeyboardLayoutOptimizer
{
    /// <summary>
    /// Core keyboard layout optimization system with genetic algorithm
    /// </summary>
    public class KeyboardLayoutOptimizer
    {
        private readonly GeneticAlgorithm _geneticAlgorithm;
        private readonly FitnessEvaluator _fitnessEvaluator;

        public KeyboardLayoutOptimizer(FitnessEvaluatorBase fitnessEvaluator)
        {
            _fitnessEvaluator = new FitnessEvaluator(fitnessEvaluator);
            _geneticAlgorithm = new GeneticAlgorithm(_fitnessEvaluator.Evaluate);
            
            // Add preset layouts
            _geneticAlgorithm.Presets.Add(new LayoutPreset("QWERTY", "abcdefghijklmnopqrstuvwxyz".ToCharArray()));
            _geneticAlgorithm.Presets.Add(new LayoutPreset("Dvorak", "aoeuidhtnsrmlqpczwbjfgkxvy".ToCharArray()));
            _geneticAlgorithm.Presets.Add(new LayoutPreset("Colemak", "qwfpgjluysemrohinctadbvkxz".ToCharArray()));
            _geneticAlgorithm.Presets.Add(new LayoutPreset("Workman", "qdrwtujfazspxbgnmveychoki".ToCharArray()));
        }

        /// <summary>
        /// Run the genetic algorithm optimization
        /// </summary>
        public OptimizationResult Optimize(int populationSize = 50, int maxGenerations = 100, int stagnationLimit = 15)
        {
            Console.WriteLine("Starting Keyboard Layout Optimization...");
            
            var result = _geneticAlgorithm.Run(populationSize, maxGenerations, stagnationLimit);
            
            Console.WriteLine($"Optimization completed in {result.ElapsedGenerations} generations");
            Console.WriteLine($"Best fitness: {result.BestIndividual.Fitness:F6}");
            Console.WriteLine($"Best layout: {new string(result.BestIndividual.Chromosome)}");
            
            return result;
        }

        /// <summary>
        /// Evaluate a specific layout configuration
        /// </summary>
        public double EvaluateLayout(char[] layout)
        {
            return _fitnessEvaluator.Evaluate(layout);
        }

        /// <summary>
        /// Compare multiple layouts
        /// </summary>
        public List<LayoutComparison> CompareLayouts(params (string name, char[] layout)[] layouts)
        {
            var comparisons = new List<LayoutComparison>();
            
            foreach (var (name, layout) in layouts)
            {
                var fitness = _fitnessEvaluator.Evaluate(layout);
                var (distance, time) = _fitnessEvaluator.CalculateComponents(layout);
                
                comparisons.Add(new LayoutComparison
                {
                    Name = name,
                    Layout = new string(layout),
                    Fitness = fitness,
                    DistanceComponent = distance,
                    TimeComponent = time
                });
            }
            
            return comparisons.OrderBy(c => c.Fitness).ToList();
        }
    }

    /// <summary>
    /// Result of the optimization process
    /// </summary>
    public class OptimizationResult
    {
        public Individual BestIndividual { get; set; }
        public int ElapsedGenerations { get; set; }
        public TimeSpan TotalTime { get; set; }
        public List<GenerationStats> GenerationHistory { get; set; } = new List<GenerationStats>();
    }

    /// <summary>
    /// Statistics for a single generation
    /// </summary>
    public class GenerationStats
    {
        public int Generation { get; set; }
        public double BestFitness { get; set; }
        public double AverageFitness { get; set; }
        public double WorstFitness { get; set; }
        public TimeSpan GenerationTime { get; set; }
    }

    /// <summary>
    /// Layout comparison result
    /// </summary>
    public class LayoutComparison
    {
        public string Name { get; set; }
        public string Layout { get; set; }
        public double Fitness { get; set; }
        public double DistanceComponent { get; set; }
        public double TimeComponent { get; set; }
    }
}