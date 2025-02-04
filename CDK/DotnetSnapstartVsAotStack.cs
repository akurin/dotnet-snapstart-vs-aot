using System;
using System.Collections.Generic;
using Amazon.CDK;
using Amazon.CDK.AWS.Lambda;
using Constructs;

namespace CDK;

public class DotnetSnapstartVsAotStack : Stack
{
    internal DotnetSnapstartVsAotStack(Construct scope, string id, IStackProps props = null)
        : base(scope, id, props)
    {
        var memorySizeString = System.Environment.GetEnvironmentVariable("FUNCTION_MEMORY_SIZE") ??
                               throw new Exception("The FUNCTION_MEMORY_SIZE environment variable is required.");

        var memorySize = int.Parse(memorySizeString);

        new Function(
            this,
            "Net8Function",
            new FunctionProps
            {
                FunctionName = $"{Aws.STACK_NAME}-Net8",
                Runtime = Runtime.DOTNET_8,
                MemorySize = memorySize,
                Timeout = Duration.Seconds(30),
                Handler = "LambdaNet8::" +
                          "LambdaNet8.Function::" +
                          "FunctionHandler",
                Code = Code.FromAsset("bin/LambdaNet8.zip"),
                Tracing = Tracing.ACTIVE
            });


        var net8AotFunction = new Function(
            this,
            "Net8SnapStartFunction",
            new FunctionProps
            {
                FunctionName = $"{Aws.STACK_NAME}-Net8SnapStart",
                Runtime = Runtime.DOTNET_8,
                MemorySize = memorySize,
                Timeout = Duration.Seconds(30),
                Handler = "LambdaNet8::" +
                          "LambdaNet8.Function::" +
                          "FunctionHandler",
                Code = Code.FromAsset("bin/LambdaNet8.zip"),
                Tracing = Tracing.ACTIVE
            });

        // SnapStart is not yet supported in the CDK
        ((CfnFunction)net8AotFunction.Node.DefaultChild)!.AddPropertyOverride(
            "SnapStart", new Dictionary<string, object>
            {
                { "ApplyOn", "PublishedVersions" }
            });

        var publishedVersion = new Version_(this, "LambdaNet8FunctionSnapStartVersion", new VersionProps
        {
            Lambda = net8AotFunction,
            Description = Guid.NewGuid().ToString() // Force cold start
        });

        new Alias(this, "LambdaNet8FunctionProdAlias", new AliasProps
        {
            AliasName = "SnapStart",
            Version = publishedVersion
        });

        new Function(
            this,
            "Net8AotFunction",
            new FunctionProps
            {
                FunctionName = $"{Aws.STACK_NAME}-Net8Aot",
                Runtime = Runtime.PROVIDED_AL2023,
                MemorySize = memorySize,
                // The Handler property is set to "unused" to avoid the following error:
                // "Missing required properties for aws-cdk-lib.aws_lambda.FunctionProps: 'handler'"
                Handler = "unused",
                Code = Code.FromAsset("bin/LambdaNet8Aot.zip"),
                Tracing = Tracing.ACTIVE,
            });
    }
}