
// {
//   "env": {
//     "ANTHROPIC_BASE_URL": "https://integrate.api.nvidia.com/v1",
//     "ANTHROPIC_AUTH_TOKEN": "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",
//     "API_TIMEOUT_MS": "3000000",
//     "ANTHROPIC_API_KEY": "",
//     "ANTHROPIC_DEFAULT_HAIKU_MODEL": "z-ai/glm4.7",
//     "ANTHROPIC_DEFAULT_SONNET_MODEL": "openai/gpt-oss-20b",
//     "ANTHROPIC_DEFAULT_OPUS_MODEL": "qwen/qwen3-coder-480b-a35b-instruct"
//   },
//   "model": "sonnet[1m]"
// }

// (Get-Command pip).Source.Replace("pip.exe", "litellm.exe")                                                                                             
// C:\Users\msilaptop\AppData\Local\Programs\Python\Python312\Scripts\litellm.exe
// PS C:\Users\msilaptop\Desktop\VinUni\lab14\Lab14-AI-Evaluation-Benchmarking> python -m C:\Users\msilaptop\AppData\Local\Programs\Python\Python312\Scripts\litellm.exe --model nvidia_nim/qwen/qwen2.5-coder-32b-instruct --drop_params
// C:\Users\msilaptop\AppData\Local\Programs\Python\Python312\python.exe: Error while finding module specification for 'C:\\Users\\msilaptop\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\litellm.exe' (ModuleNotFoundError: No module named 'C:\\Users\\msilaptop\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\litellm')
// PS C:\Users\msilaptop\Desktop\VinUni\lab14\Lab14-AI-Evaluation-Benchmarking> "C:\Users\msilaptop\AppData\Local\Programs\Python\Python312\Scripts\litellm.exe" --model nvidia_nim/qwen/qwen2.5-coder-32b-instruct --drop_params      
// ParserError: 
// Line |
//    1 |  … \Local\Programs\Python\Python312\Scripts\litellm.exe" --model nvidia_ …
//      |                                                            ~~~~~
//      | Unexpected token 'model' in expression or statement.
// PS C:\Users\msilaptop\Desktop\VinUni\lab14\Lab14-AI-Evaluation-Benchmarking> & "C:\Users\msilaptop\AppData\Local\Programs\Python\Python312\Scripts\litellm.exe" --model nvidia_nim/nvidia/qwen2.5-coder-32b-instruct --drop_params