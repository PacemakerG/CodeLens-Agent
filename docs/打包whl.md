

**打包**

```bash
pip wheel . --no-deps --no-build-isolation -w dist/
# 生成 dist/deep_ai_analysis-0.1.0-py3-none-any.whl
```

**上传whl包和安装脚本（如果install.sh有变更）**

安装脚本和whl文件放在[测试环境s3 ad-dqe-public/ai-coding-analysis](https://s3plus.mws-test.sankuai.com/bucket-detail/beijing/com.sankuai.wmadbizcharge.bizad.aegis/ad-dqe-public/objects/ai-coding-analysis%2F?project_id=)


