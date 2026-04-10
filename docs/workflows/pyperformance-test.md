# PyPerformance测试工作流

## 真实环境测试命令

在执行性能测试时务必参考真实环境测试，避免测试命令参数差异导致的结果偏差。

### 测试套执行

主要参考环境变量、warmup及inherit-environ的值。

```shell
PYTHONJITENABLEJITLISTWILDCARDS=1 PYTHONJITLISTFILE=/home/jit_list.txt PYTHONPATH="$PWD/scripts/arm/pyperf_env_hook:$PYTHONPATH" PYTHONJITTYPEANNOTATIONGUARDS=1 PYTHONJITENABLEHIRINLINER=1 PYTHONJITAUTO=2 PYTHONJITSPECIALIZEDOPCODES=1 python -m pyperformance run --affinity=262 --warmup 3 -b regex_compile --inherit-environ http_proxy,https_proxy,LD_LIBRARY_PATH,PYTHONJITAUTO,PYTHONJITSPECIALIZEDOPCODES,PYTHONJITENABLEHIRINLINER,PYTHONJITTYPEANNOTATIONGUARDS,PYTHONPATH,PYTHONJITLISTFILE,PYTHONJITENABLEJITLISTWILDCARDS
```

### 单独执行

主要参考环境变量和run_benchmark.py的入参。

```shell
PYTHONJITENABLEJITLISTWILDCARDS=1 PYTHONJITLISTFILE=/home/jit_list.txt PYTHONPATH="$PWD/scripts/arm/pyperf_env_hook:$PYTHONPATH" PYTHONJITDUMPHIR=1 PYTHONJITDUMPSTATS=1 PYTHONJITLOGFILE="/home/jit-go.log" PYTHONJITDUMPFINALHIR=1 PYTHONJITTYPEANNOTATIONGUARDS=1 PYTHONJITENABLEHIRINLINER=1 PYTHONJITAUTO=2 PYTHONJITSPECIALIZEDOPCODES=1 python /usr/local/lib/python3.14/site-packages/pyperformance/data-files/benchmarks/bm_go/run_benchmark.py --worker -l5 -w11 -n2
```

### JIT白名单

```text
__main__:*
copy:* 
pickle:*
tomli._parser:*
django.template:*
django.template.base:*
django.template.context:*
django.template.engine:*
django.template.library:*
django.template.defaulttags:*
django.template.defaultfilters:*
django.template.loader_tags:*
django.template.smartif:*
django.utils:*
django.utils.safestring:*
django.utils.encoding:*
django.utils.html:*
django.utils.itercompat:*
django.utils.text:*
django.utils.regex_helper:*
django.utils.autoreload:*
```

## TroubleShooting

