# 浏览器截图与 manifest

在开始截图时读本文件。此流程只读取网页实际展示的曲谱，不下载隐藏资源。浏览器交互遵循当前工具提供的文档；以下 CUA 示例已在本环境验证其核心接口，不适用于直接粘贴到其他浏览器运行时。

## 定位和拍摄

1. 用当前浏览器打开用户链接，读页面状态确认标题和总页数。不要凭 URL 推断曲名。
2. MuseScore 当前的谱面 `<img>` 的可访问名称类似 `… – 1 of 2 pages`。可以用 `getByRole('img', {name: /\d+ of \d+ pages/})` 定位，再读取 `getBoundingClientRect()`、`complete` 和 `naturalWidth`。若页面结构改变，重新检查实际 DOM/截图并更新定位，不能从内部状态或网络猜测页图地址。
3. 从截图和可见 DOM 边界确定 `safe_rect`：谱面滚动区中真正未被工具栏、提示等覆盖的矩形，固定栏底部的分隔线也应排除。必须横向包含整张谱纸。一个提示气泡也可能只遮住纸边一小块，先点击空白区域或正常关闭提示，再检查实际保存的截图。
4. 用与 DOM 坐标匹配的 `tab.screenshot({fullPage:false})` 保存截图。当前浏览器返回 JPEG，因此临时文件用 `.jpg`；不要只改扩展名冒充 PNG。最终由 Python 重新编码为 PNG。其他截图 API 若确实返回 PNG，则保存 `.png`。
5. 滚动约半个视口，检查新状态、等待页图加载后再拍。重叠应包含足够谱面以检查连续性。新一页开始时也需要记录整页边界，包括原有留白。

截图中出现白色纸张但 `complete` 为 true，也不保证拍到了有效音符：看截图。第二页可能只有一行谱，下面大段留白是正常的。完整截图后再视觉确认。

不要临时调整浏览器视口来塞下整页。滚动截图即可。若窗口或谱面缩放发生变化，重新拍摄受影响的那一页；不要用猜测缩放比例拼接。

## 减少耗时

初始页面已检查、缩放和安全区域稳定后，把已确定的“滚动 → 读取新状态 → 记录边界并保存截图”在一次工具调用中顺序执行，减少模型与工具之间的往返。仍需在每次滚动后检查状态；页图未加载、页号不符或出现遮挡时退出批次，检查后再继续。

根据已覆盖的谱面区间决定下一次滚动，保留必要重叠，避免反复回滚和多拍同一区域。普通中间步骤返回页号、覆盖区间等短摘要即可；初始状态、异常情况和最终拼接预览保留视觉检查。不要在每一步重复输出整棵页面树和整屏图片。

为每份曲谱创建独立采集会话对象，并显式传给记录函数，避免持久 REPL 中复用旧闭包，把新截图写进上一份曲谱的 manifest。PNG 拼接通常只占很少时间，优先减少网页交互和补拍。

## CUA 记录示例

先用 `cua_repl` 初始化/恢复文档，并阅读浏览器和 screenshots 文档。复用当前浏览器会话和 tab。可用下列函数保存每个经过视觉检查的视口；函数不执行滚动或自动判断安全区域。

```javascript
// 在 cua_repl 中执行。tab 是已打开且确认过的曲谱标签页。
// 使用本次任务的临时目录，最终保存目录必须另行按用户要求确认。
var captureFs = await import('node:fs/promises');
var captureRoot = '/tmp/musescore-capture-本次任务唯一标识';
await captureFs.mkdir(captureRoot, {recursive: true});
var captureManifest = {
  title: '从页面确认的曲名',
  page_count: 2, // 从页面核实，不按当前已加载的图数猜测
  captures: [],
  blank_edges: {}
};
var captureSession = {root: captureRoot, manifest: captureManifest};

var recordScoreViewport = async function(tab, safeRect, session) {
  var viewport = await tab.playwright.evaluate(() => ({
    width: window.innerWidth, height: window.innerHeight
  }));
  var pageImages = await tab.playwright
    .getByRole('img', {name: /\d+ of \d+ pages/})
    .evaluateAll(elements => elements.map(el => ({
      alt: el.getAttribute('alt'),
      complete: el.complete && el.naturalWidth > 0,
      rect: el.getBoundingClientRect().toJSON()
    })));
  var pages = [];
  for (var entry of pageImages) {
    var match = (entry.alt || '').match(/(\d+) of (\d+) pages/);
    if (!match) continue;
    if (Number(match[2]) !== session.manifest.page_count) {
      throw new Error('页数发生变化，请重新检查页面');
    }
    var r = entry.rect;
    var overlaps = r.bottom > safeRect.y && r.top < safeRect.y + safeRect.height;
    if (!overlaps) continue;
    if (!entry.complete) throw new Error('可见谱页尚未加载完成');
    pages.push({number: Number(match[1]), paper_rect: {
      x: r.x, y: r.y, width: r.width, height: r.height
    }});
  }
  if (!pages.length) throw new Error('当前视口没有已加载谱页，请检查页面');
  var filename = `capture-${session.manifest.captures.length + 1}.jpg`;
  await captureFs.writeFile(session.root + '/' + filename,
    await tab.screenshot({fullPage: false}));
  session.manifest.captures.push({image: filename, viewport,
    safe_rect: safeRect, pages});
  await captureFs.writeFile(session.root + '/manifest.json',
    JSON.stringify(session.manifest, null, 2));
};
```

每次滚动/关闭浮层后先读取新状态，再确定 `safeRect`，调用 `recordScoreViewport(tab, safeRect, captureSession)`。每份曲谱使用自己的会话对象。安全区域改变时重新记录，不能复用过期坐标。检查已保存截图与记录是否对应；纸张在运动、截图与边界错位时丢弃该次记录并补拍。

## Manifest 契约

`stitch_score.py` 接收一个曲谱的 JSON：

```json
{
  "title": "女儿情",
  "page_count": 1,
  "captures": [
    {
      "image": "capture-1.jpg",
      "viewport": {"width": 1200, "height": 900},
      "safe_rect": {"x": 0, "y": 100, "width": 1000, "height": 800},
      "pages": [
        {"number": 1, "paper_rect": {"x": 100, "y": 100, "width": 800, "height": 1200}}
      ]
    },
    {
      "image": "capture-2.jpg",
      "viewport": {"width": 1200, "height": 900},
      "safe_rect": {"x": 0, "y": 100, "width": 1000, "height": 800},
      "pages": [
        {"number": 1, "paper_rect": {"x": 100, "y": -500, "width": 800, "height": 1200}}
      ]
    }
  ]
}
```

这些数字仅说明格式，不能当作实际网页坐标。`image` 相对于 manifest 所在目录，也可用本地绝对路径。`viewport`、`safe_rect`、`paper_rect` 全用 CSS 视口坐标；脚本根据截图实际像素计算设备倍率，支持常见的 1×/2× 截图。`pages` 只列该张截图安全区域内实际加载的谱页，同张截图可以包含相邻两页。

`page_count` 必须为正整数；页号从 1 连续到总页数，每张截图的页号不能重复。`safe_rect` 要在视口内，横向包含完整纸张，竖向排除所有覆盖物。脚本可以处理被视口上下裁切的纸张，但不会合成缺失谱面。

默认不允许任何未覆盖行。若确认纸边被工具栏挡住的几像素完全是留白，可显式补充：

```json
"blank_edges": {"1": {"top": 6}, "2": {"bottom": 1}}
```

这里是最终输出的**物理像素数**，不是 CSS 像素。只支持顶部/底部已确认的空白，不支持中间填白。无法确认时补拍，不要为了消除覆盖报错而增大补白范围。

脚本只在全部页通过验证后发布曲名目录。它会排除边界的亚像素混色、选择重叠中的空白带作接缝；不做 OCR、去水印、锐化、音符重绘或内容推断。最终仍需查看谱面首尾、每页边缘和接缝。输出目录存在时不覆盖，应先获得用户选择的新目录或名称。
