using System;

namespace TestErgoType
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Testing basic C# functionality...");
            
            // Test basic types
            var keyboard = new ErgoType.Core.KeyboardFactory().CreateAnsi60Percent();
            Console.WriteLine($"Created keyboard: {keyboard.Name}");
            
            // Test layout creation
            var layout = ErgoType.Core.KeyboardLayout.Create("test", "qwertyuiopasdfghjklzxcvbnm".ToCharArray());
            Console.WriteLine($"Created layout: {layout}");
            
            // Test individual creation
            var individual = new ErgoType.Core.Individual(1, "test", layout, 0);
            Console.WriteLine($"Created individual: {individual}");
            
            // Test fitness evaluation
            var config = new ErgoType.Core.Fitness.FitnessConfig();
            var evaluator = new ErgoType.Core.Fitness.SimplifiedFitnessEvaluator(config);
            var result = evaluator.Evaluate(layout, keyboard);
            Console.WriteLine($"Fitness result: {result.Fitness:F6}");
            
            Console.WriteLine("All tests passed!");
        }
    }
}