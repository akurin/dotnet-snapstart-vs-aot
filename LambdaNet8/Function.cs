using Amazon.Lambda.Core;

[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace LambdaNet8;

public class Function
{
    public string FunctionHandler(string input, ILambdaContext context) => input.ToUpper();
}