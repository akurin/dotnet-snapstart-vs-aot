using Amazon.Lambda.Core;
using Amazon.Lambda.RuntimeSupport;
using Amazon.Lambda.Serialization.SystemTextJson;

namespace LambdaNet8Aot;

public static class EntryPoint
{
    public static async Task Main()
    {
        await LambdaBootstrapBuilder.Create<string, string>(Handler,
                new SourceGeneratorLambdaJsonSerializer<LambdaJsonSerializerContext>())
            .Build()
            .RunAsync();
    }

    private static Task<string> Handler(string input, ILambdaContext context) => Task.FromResult(input.ToUpper());
}