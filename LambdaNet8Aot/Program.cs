using Amazon.Lambda.Core;
using Amazon.Lambda.RuntimeSupport;
using Amazon.Lambda.Serialization.SystemTextJson;

namespace LambdaNet8Aot;

public class EntryPoint
{
    public static async Task Main()
    {
        await LambdaBootstrapBuilder.Create<string>(Handler,
                new SourceGeneratorLambdaJsonSerializer<InputJsonSerializerContext>())
            .Build()
            .RunAsync();
    }

    private static Task<string> Handler(string input, ILambdaContext context) => Task.FromResult(input.ToUpper());
}