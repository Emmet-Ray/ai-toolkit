# 黑白叙事剪影

“叙事剪影”是工作名称，用来描述以黑白形状及其关系概括含义的图案，并非严格的艺术流派。统一视觉处理，根据内容改变主体与构图。

## 视觉参考

查看 [已确认的风格样图](../assets/narrative-silhouette-reference.png)：书页汇成飞鸟，表达从内容中提炼出一个鲜明意象。参考其黑白关系、形状概括和边缘质感；书、飞鸟及其组合属于这一张的内容，不是所有图片的固定构图。不要默认把单一主体的样图作为每次生成的图像输入，以免继承参考图的主体或布局；文字风格约束足够时可直接生成。

主要方向来自用户提供的《Braid》关卡选择门板上的黑色小画：物体、钥匙与锁、平台、火焰、生物和植物等，可以通过轮廓、排列、间距与正负形构成不同的小场景。共性是符号化和黑白关系，主体不固定。使用原创构图；门框、云雾、水彩背景均不是本预设的必要元素。

## 默认规则

- 单张方图，白底、实黑主体，默认不画标题、说明或水印。语言、命令行等含义仅靠轮廓难以辨识时，可以保留最少必要的功能符号，例如 `EN`、`中` 或 `>_`；放大到缩略图中仍清楚，不加长句或装饰文字。
- 用少量剪影形状组成一个有含义的图案或小场景。主体可为物件、生物、植物、空间结构或抽象形态；根据内容选择，不预设职业人物、儿童或固定主角。
- 优先用物体之间的关系、形状转换、包含、分离、呼应或空间张力概括核心。只有画面含义需要时才出现人物；无需以人物操作工具来解释所有功能。
- 大色块优先，用有意留出的白色空隙分开关键形状，避免合成难以辨认的黑团。轮廓允许概括、夸张、适度不对称，保持符号感，不追求职业动作的写实细节。
- 轮廓略有手工剪切或模板印刷的不规则感；只在边缘保留少量干墨质感。不要加细密刻线、内部明暗、渐变、投影或复杂机械细节。
- 在统一画幅内保持相近的视觉体量与留白；可按含义使用纵向、横向、对置或包围构图，不固定为“左边人物、右边工具”。保持完整轮廓，不贴边，不靠过多细小碎片表达概念。
- 在约 180 像素的展示宽度下仍能看出主要动作。必要时减少装饰和内线，保留最有辨识度的轮廓。

允许用户更换背景色、反转前景与背景、使用透明底或增加统一边框。颜色变化仍应保留强烈的明度对比；不要把全系列一致性理解为所有图片必须同一个主体或同一个动作。

## 提示词骨架

将下面的可变内容替换为本次内容的核心及画面关系。风格段不包含人物身份、年龄、职业或姿态。需要参考图片时，优先选能体现当前构图范围的参考；明确只继承视觉特征。

```text
Create one symbolic silhouette vignette summarizing [CORE MEANING].
Composition: [ESSENTIAL SHAPES AND THE RELATIONSHIP THAT EXPRESSES THE MEANING].
Use bold black masses on a clean white field, expressive simplified contours and deliberate white negative spaces. Give the edges a subtle hand-cut, stencil-painted irregularity with restrained dry-ink roughness. Keep the design compact and readable as a small painted emblem. Arrange the shapes to express this specific meaning; no recurring protagonist or default human figure is required.
Square canvas, generous margins, no shading, hatching, gradients, drop shadows, 3D, fine decorative details, titles, explanatory captions or watermark. Include only the functional symbols explicitly specified in the composition when they are necessary to identify the meaning; otherwise omit lettering. No door, decorative frame or background scenery unless requested.
```

使用图像参考时，额外写明：`Use the supplied image only for black-and-white treatment, edge texture and simplification. Do not inherit its characters, age, pose, props or composition.`

## 系列区分示例

- `musescore-snapper`：乐谱被取景框收拢，并形成叠放的图片，概括谱面采集与保存。
- `image-generator`：画笔与画框中的月亮、山丘产生呼应，概括画面生成。
- `tldr-en-page-maintainer`：带 `>_` 和 `EN` 标记的简明命令页与修改笔，概括维护英文命令说明；仅用书或放大镜难以表达命令行领域。
- `tldr-zh-page-maintainer`：两份同样带 `>_` 的对应命令页，以 `EN`、`中` 标记和转换关系表达翻译；避免以抽象横线和方块代替语言，导致含义不清。
- `visual-summarizer`：多层书页收拢成一只飞鸟的轮廓，概括从内容提炼出一个鲜明意象。

这些是当前仓库的构思示例，不应作为所有内容的固定映射。
