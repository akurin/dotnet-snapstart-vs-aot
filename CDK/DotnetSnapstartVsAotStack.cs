using System.Collections.Generic;
using Amazon.CDK;
using Amazon.CDK.AWS.Lambda;
using Constructs;

namespace CDK
{
    public class DotnetSnapstartVsAotStack : Stack
    {
        internal DotnetSnapstartVsAotStack(Construct scope, string id, IStackProps props = null)
            : base(scope, id, props)
        {
            new Function(
                this,
                "LambdaNet8Function",
                new FunctionProps
                {
                    FunctionName = $"{Aws.STACK_NAME}-LambdaNet8",
                    Runtime = Runtime.DOTNET_8,
                    MemorySize = 1024,
                    Timeout = Duration.Seconds(30),
                    Handler = "LambdaNet8::" +
                              "LambdaNet8.Function::" +
                              "FunctionHandler",
                    Code = Code.FromAsset("bin/LambdaNet8.zip"),
                    Tracing = Tracing.ACTIVE
                });

            var snapStartFunction = new Function(
                this,
                "LambdaNet8FunctionSnapStart",
                new FunctionProps
                {
                    FunctionName = $"{Aws.STACK_NAME}-LambdaNet8SnapStart",
                    Runtime = Runtime.DOTNET_8,
                    MemorySize = 1024,
                    Timeout = Duration.Seconds(30),
                    Handler = "LambdaNet8::" +
                              "LambdaNet8.Function::" +
                              "FunctionHandler",
                    Code = Code.FromAsset("bin/LambdaNet8.zip"),
                    Tracing = Tracing.ACTIVE
                });

            // SnapStart is not yet supported in the CDK
            ((CfnFunction)snapStartFunction.Node.DefaultChild)!.AddPropertyOverride(
                "SnapStart", new Dictionary<string, object>
                {
                    { "ApplyOn", "PublishedVersions" }
                });

            new Version_(this, "LambdaNet8FunctionSnapStartVersion", new VersionProps
            {
                Lambda = snapStartFunction
            });
        }
    }
}