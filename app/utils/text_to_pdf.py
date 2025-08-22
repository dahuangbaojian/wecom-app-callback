import logging
import os
import re
import uuid
from datetime import datetime
from typing import List, Optional

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

# 使用app logger，确保日志能正确输出到app.log
logger = logging.getLogger(__name__)


def setup_chinese_fonts():
    """注册字体：优先使用系统字体，回退到内置字体"""
    try:
        # 1. 尝试使用系统字体
        import platform

        system = platform.system()
        logger.info(f"🔍 字体检测开始 - 系统: {system}")

        if system == "Darwin":  # macOS
            system_fonts = [
                "/System/Library/Fonts/STHeiti Light.ttc",  # 华文黑体 Light
                "/System/Library/Fonts/STHeiti Medium.ttc",  # 华文黑体 Medium
                "/System/Library/Fonts/ArialHB.ttc",  # Arial HB
                "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",  # ヒラギノ角ゴシック
                "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc",  # ヒラギノ明朝
                "/Library/Fonts/Arial Unicode MS.ttf",  # 用户安装的字体
                "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",  # ヒラギノ角ゴシック W3
                "/System/Library/Fonts/ヒラギノ角ゴシック W5.ttc",  # ヒラギノ角ゴシック W5
            ]
        elif system == "Linux":  # Linux
            system_fonts = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # DejaVu Sans
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Liberation Sans
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Noto Sans CJK
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",  # Ubuntu
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",  # FreeSans
                "/usr/share/fonts/truetype/arphic/uming.ttc",  # AR PL UMing
                "/usr/share/fonts/truetype/arphic/ukai.ttc",  # AR PL UKai
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # 文泉驿微米黑
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # 文泉驿正黑
            ]

            # Linux系统字体安装建议
            logger.debug("🐧 Linux系统检测到，建议安装中文字体包：")
            logger.debug(
                "Ubuntu/Debian: sudo apt-get install fonts-wqy-microhei fonts-wqy-zenhei"
            )
            logger.debug(
                "CentOS/RHEL: sudo yum install wqy-microhei-fonts wqy-zenhei-fonts"
            )
            logger.debug("或者: sudo yum install google-noto-sans-cjk-fonts")
        else:  # Windows 或其他系统
            system_fonts = [
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
            ]

        # 尝试注册系统字体
        for font_path in system_fonts:
            if os.path.exists(font_path):
                try:
                    # 尝试注册TTF字体
                    font_name = f"SystemFont_{os.path.basename(font_path)}"
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    logger.debug(f"✅ 成功注册系统字体: {font_path}")

                    # 对于Linux系统，检查是否找到了中文字体
                    if system == "Linux":
                        # 检查字体是否支持中文（通过检查字体名称或路径）
                        if any(
                            keyword in font_path.lower()
                            for keyword in ["noto", "wqy", "arphic", "uming", "ukai"]
                        ):
                            logger.debug(f"✅ 找到中文字体: {font_path}")
                            return font_name
                        else:
                            logger.warning(
                                f"⚠️ 字体 {font_path} 可能不支持中文，继续尝试其他字体"
                            )
                            continue
                    else:
                        return font_name

                except Exception as e:
                    logger.debug(f"注册字体失败 {font_path}: {e}")
                    continue

        # 2. 回退到 reportlab 内置字体
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            logger.debug("✅ 成功注册内置字体: STSong-Light（支持中文）")
            return "STSong-Light"
        except Exception as e:
            logger.debug(f"内置字体注册失败: {e}")

        # 3. 最后回退到 Helvetica
        logger.warning("⚠️ 无法找到中文字体，使用 Helvetica（不支持中文，可能出现乱码）")
        return "Helvetica"

    except Exception as e:
        logger.error(f"字体设置失败: {e}")
        return "Helvetica"


def clean_markdown_content(content: str) -> str:
    """清理markdown内容，移除HTML标签和无效内容"""
    # 清理多余的空行
    content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

    # 清理HTML标签，包括颜色标签
    content = re.sub(r'<font\s+color="[^"]*">(.*?)</font>', r"\1", content)
    content = re.sub(r"<[^>]+>", "", content)

    # 清理可能的特殊字符 - 保留更多有用的标点符号
    content = re.sub(
        r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef.,!?;:()\[\]{}"\'-_+=<>/\\|@#$%^&*~`]',
        "",
        content,
    )

    return content


def parse_markdown_with_linebreaks(content: str) -> List[str]:
    """将markdown内容解析为段落列表，保持原始换行格式"""
    # 直接分割原始内容，保持换行
    paragraphs = []
    lines = content.split("\n")

    for line in lines:
        if line.strip():
            paragraphs.append(line)
        else:
            # 空行也作为一个段落，保持换行
            paragraphs.append("")

    return paragraphs


def create_pdf_styles():
    """创建PDF样式"""
    styles = getSampleStyleSheet()

    # 设置字体 - 优先使用中文字体
    font_name = setup_chinese_fonts()
    logger.debug(f"使用字体: {font_name}")

    # 自定义样式
    styles.add(
        ParagraphStyle(
            name="CustomTitle",
            parent=styles["Heading1"],
            fontName=font_name,
            fontSize=18,
            spaceAfter=30,
            textColor=HexColor("#1a1a1a"),
            alignment=1,  # 居中
            leading=22,  # 标题行间距
        )
    )

    styles.add(
        ParagraphStyle(
            name="CustomHeading",
            parent=styles["Heading2"],
            fontName=font_name,
            fontSize=16,
            spaceAfter=20,
            textColor=HexColor("#2c3e50"),
            leading=20,  # 副标题行间距
        )
    )

    styles.add(
        ParagraphStyle(
            name="CustomBody",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=13,
            spaceAfter=10,
            textColor=HexColor("#333333"),
            leading=20,  # 增加行间距
            wordWrap="LTR",  # 左到右换行
            splitLongWords=1,  # 允许长单词换行
            keepWithNext=0,  # 不强制保持与下一段在一起
            wordSpace=0.3,  # 增加单词间距
            characterSpacing=0.8,  # 增加字符间距
        )
    )

    styles.add(
        ParagraphStyle(
            name="CustomBlockquote",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=12,
            leftIndent=24,
            spaceAfter=8,
            textColor=HexColor("#7f8c8d"),
            leading=18,  # 引用块行间距
        )
    )

    # 添加颜色样式

    return styles


def text_to_pdf(
    content: str, output_dir: str = "data/pdf_files", filename_prefix: str = "response"
) -> Optional[str]:
    """
    直接将文本内容转换为PDF

    Args:
        content: 要转换的文本内容
        output_dir: PDF输出目录
        filename_prefix: 文件名前缀

    Returns:
        PDF文件路径，如果失败返回None
    """
    try:
        # 检查输入内容
        if not content or not content.strip():
            logger.warning("输入内容为空，无法生成PDF")
            return None

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 检查内容长度，如果太长则截断
        if len(content) > 50000:  # 50KB限制
            logger.warning(f"内容过长({len(content)}字符)，将截断到50000字符")
            content = content[:50000] + "\n\n... (内容已截断)"

        # 清理内容
        cleaned_content = clean_markdown_content(content)

        # 检查清理后的内容
        if not cleaned_content or not cleaned_content.strip():
            logger.warning("清理后的内容为空，无法生成PDF")
            return None

        # 解析为段落，保持原始换行格式
        paragraphs = parse_markdown_with_linebreaks(cleaned_content)

        # 生成PDF文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = str(uuid.uuid4())[:8]
        pdf_filename = f"{filename_prefix}_{timestamp}_{file_id}.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)

        # 创建PDF文档，启用字体嵌入
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
            initialFontSize=12,
        )
        styles = create_pdf_styles()

        # 构建PDF内容
        story = []

        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                # 空行，添加适当的间距
                story.append(Spacer(1, 8))
                continue

            # 判断段落类型并应用相应样式
            if paragraph.startswith("# "):
                text = paragraph[2:].strip()
                story.append(Paragraph(text, styles["CustomTitle"]))
            elif paragraph.startswith("## "):
                text = paragraph[3:].strip()
                story.append(Paragraph(text, styles["CustomHeading"]))
            elif paragraph.startswith("### "):
                text = paragraph[4:].strip()
                story.append(Paragraph(text, styles["CustomHeading"]))
            elif paragraph.startswith("> "):
                # 处理引用块
                text = paragraph[2:].strip()
                story.append(Paragraph(text, styles["CustomBlockquote"]))
            elif paragraph.startswith("- ") or paragraph.startswith("* "):
                # 处理列表项
                text = paragraph[2:].strip()
                story.append(Paragraph(text, styles["CustomBody"]))
            elif (
                paragraph.startswith("1. ")
                or paragraph.startswith("2. ")
                or paragraph.startswith("3. ")
                or paragraph.startswith("4. ")
                or paragraph.startswith("5. ")
            ):
                # 处理有序列表项
                text = re.sub(r"^\d+\.\s*", "", paragraph)
                story.append(Paragraph(text, styles["CustomBody"]))
            else:
                # 普通文本
                story.append(Paragraph(paragraph, styles["CustomBody"]))

            # 只在非空段落后添加小间距，保持紧凑
            if i < len(paragraphs) - 1 and paragraphs[i + 1].strip():
                story.append(Spacer(1, 3))

        # 生成PDF
        try:
            logger.info(
                f"开始生成PDF，内容长度: {len(content)} 字符，段落数: {len(paragraphs)}"
            )
            doc.build(story)
            logger.info(f"PDF文件已生成: {pdf_path}")
            return pdf_path
        except Exception as build_error:
            logger.error(f"PDF构建失败: {build_error}")
            logger.error(f"失败内容预览: {cleaned_content[:200]}...")

            # 如果PDF生成失败，回退到文本文件
            try:
                logger.info("PDF生成失败，回退到文本文件...")
                txt_path = pdf_path.replace(".pdf", ".txt")
                # 使用已经清理过的内容
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(cleaned_content)
                logger.info(f"文本文件已生成: {txt_path}")
                return txt_path
            except Exception as txt_error:
                logger.error(f"文本文件生成也失败: {txt_error}")
                return None

    except Exception as e:
        logger.error(f"转换失败: {e}")
        return None
