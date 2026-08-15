"""
Internationalization (i18n) module for NikkiBook.
Provides translations for English, Chinese (Simplified), and Japanese.
Language changes are broadcast to all registered listeners without restart.
"""
from PyQt6.QtCore import QObject, pyqtSignal, QLocale, QSettings

# ---------------------------------------------------------------------------
# Translation strings
# ---------------------------------------------------------------------------
TRANSLATIONS = {
    "en": {
        # Main window header
        "search_placeholder": "Search by name, category, or sharecode...",
        "sort_label": "Sort:",
        "sort_newest": "Newest First",
        "sort_oldest": "Oldest First",
        "sort_name": "Name A-Z",
        "add_image_btn": "+ Add Image",

        # Sidebar / category tree
        "add_category_btn": "+ Category",
        "add_subcategory_btn": "+ Subcategory",
        "show_all_btn": "Show All Images",

        # Dialogs – shared
        "cancel": "Cancel",
        "save": "Save",

        # AddCategoryDialog
        "add_category_title": "Add Category",
        "category_name_label": "CATEGORY NAME",
        "category_name_placeholder": "Enter category name...",
        "create_category_btn": "Create Category",

        # AddSubcategoryDialog
        "add_subcategory_title": "Add Subcategory",
        "parent_category_label": "PARENT CATEGORY",
        "subcategory_name_label": "SUBCATEGORY NAME",
        "subcategory_name_placeholder": "Enter subcategory name...",
        "create_subcategory_btn": "Create Subcategory",

        # AddImageDialog / EditImageDialog
        "add_image_title": "Add Image",
        "edit_image_title": "Edit Image",
        "select_file_label": "SELECT FILE",
        "no_file_selected": "No file selected",
        "browse_btn": "Browse...",
        "display_name_label": "DISPLAY NAME (OPTIONAL)",
        "display_name_label_required": "DISPLAY NAME",
        "display_name_placeholder": "Enter display name...",
        "category_label": "CATEGORY",
        "subcategory_label": "SUBCATEGORY",
        "none_option": "(None)",
        "sharecode_label": "SHARECODE (OPTIONAL)",
        "sharecode_label_required": "SHARECODE",
        "sharecode_placeholder": "Enter sharecode...",
        "add_image_ok_btn": "Add Image",
        "save_changes_btn": "Save Changes",

        # RenameDialog
        "rename_category_title": "Rename Category",
        "rename_subcategory_title": "Rename Subcategory",
        "new_name_label": "NEW NAME",
        "rename_btn": "Rename",

        # SnapProgressDialog
        "snap_title": "Snap Capture",
        "snap_initializing": "Initializing...",
        "snap_step": "Step {step} / 10",
        "snap_window_title": "Snap in Progress",

        # SettingsDialog
        "settings_title": "Settings",
        "snap_mode_label": "Snap workflow mode:",
        "snap_mode_album": "Mode 1: Add to album",
        "snap_mode_nikkibook": "Mode 2: Save to NikkiBook only",
        "capture_area_label": "Screenshot capture area (pixels):",
        "capture_width_label": "Width",
        "capture_height_label": "Height",
        "capture_offset_label": "Left offset",
        "capture_default_hint": "Leave blank to use 450 × 600 px with a 450 px left offset.",
        "language_label": "Interface language:",
        "snap_visibility_label": "Snap (beta testing):",
        "snap_visible": "Show",
        "snap_hidden": "Hide",

        # Settings footnote
        "settings_footnote_author": "Created by Triii Yukari · leaving my footprints with Nikki!",
        "settings_footnote_coffee": "https://buymeacoffee.com/triiitri",

        # ImageDetailsModal
        "edit_details_title": "Edit Details",
        "info_title": "INFO",
        "id_label": "ID: —",
        "added_label": "Added: —",
        "added_prefix": "Added:",
        "delete_image_btn": "Delete Image",

        # Warnings / errors
        "no_categories_title": "No Categories",
        "no_categories_msg": "Please create a category first before adding images.",
        "no_categories_snap_msg": "Please create a category first before using Snap.",
        "update_error_title": "Update Error",
        "delete_error_title": "Delete Error",
        "import_error_title": "Import Error",
        "import_errors_title": "Import Errors",
        "paste_error_title": "Paste Error",
        "paste_no_image": "No valid image in clipboard.",
        "snap_error_title": "Snap Error",
        "snap_no_categories": "No categories available to save the image.",
        "snap_import_error": "Snap Import Error",
        "validation_error_title": "Validation Error",
        "validation_name_empty": "Category name cannot be empty.",
        "validation_subname_empty": "Subcategory name cannot be empty.",
        "validation_select_category": "Please select a parent category.",
        "validation_select_file": "Please select an image file.",
        "validation_select_image_category": "Please select a category.",
        "validation_name_cannot_be_empty": "Name cannot be empty.",
        "confirm_delete_title": "Delete {item_type}",
        "confirm_delete_msg": "Are you sure you want to delete '{item_name}'?\n\nThis action cannot be undone.",

        # Context menu
        "rename_action": "Rename",
        "delete_action": "Delete",

        # Errors in category tree
        "error_title": "Error",
        "error_create_category": "Failed to create category: {error}",
        "error_create_subcategory": "Failed to create subcategory: {error}",
        "error_rename": "Failed to rename: {error}",
        "error_delete": "Failed to delete: {error}",
        "error_no_categories": "Please create a category first.",

        # Copy tooltip
        "copy_tooltip": "Copy to clipboard",
    },

    "zh": {
        "search_placeholder": "按名称、分类或分享码搜索…",
        "sort_label": "排序：",
        "sort_newest": "最新优先",
        "sort_oldest": "最旧优先",
        "sort_name": "名称 A-Z",
        "add_image_btn": "+ 添加图片",

        "add_category_btn": "+ 分类",
        "add_subcategory_btn": "+ 子分类",
        "show_all_btn": "显示全部图片",

        "cancel": "取消",
        "save": "保存",

        "add_category_title": "添加分类",
        "category_name_label": "分类名称",
        "category_name_placeholder": "输入分类名称…",
        "create_category_btn": "创建分类",

        "add_subcategory_title": "添加子分类",
        "parent_category_label": "父级分类",
        "subcategory_name_label": "子分类名称",
        "subcategory_name_placeholder": "输入子分类名称…",
        "create_subcategory_btn": "创建子分类",

        "add_image_title": "添加图片",
        "edit_image_title": "编辑图片",
        "select_file_label": "选择文件",
        "no_file_selected": "未选择文件",
        "browse_btn": "浏览…",
        "display_name_label": "显示名称（可选）",
        "display_name_label_required": "显示名称",
        "display_name_placeholder": "输入显示名称…",
        "category_label": "分类",
        "subcategory_label": "子分类",
        "none_option": "（无）",
        "sharecode_label": "分享码（可选）",
        "sharecode_label_required": "分享码",
        "sharecode_placeholder": "输入分享码…",
        "add_image_ok_btn": "添加图片",
        "save_changes_btn": "保存更改",

        "rename_category_title": "重命名分类",
        "rename_subcategory_title": "重命名子分类",
        "new_name_label": "新名称",
        "rename_btn": "重命名",

        "snap_title": "截图捕获",
        "snap_initializing": "正在初始化…",
        "snap_step": "步骤 {step} / 10",
        "snap_window_title": "截图进行中",

        "settings_title": "设置",
        "snap_mode_label": "截图工作流模式：",
        "snap_mode_album": "模式 1：添加到星绘图册",
        "snap_mode_nikkibook": "模式 2：仅保存到 NikkiBook",
        "capture_area_label": "截图区域（像素）：",
        "capture_width_label": "宽度",
        "capture_height_label": "高度",
        "capture_offset_label": "向左偏移",
        "capture_default_hint": "留空则使用默认值 450 × 600 像素，并向左偏移 450 像素。",
        "language_label": "界面语言：",
        "snap_visibility_label": "Snap（测试功能）：",
        "snap_visible": "显示",
        "snap_hidden": "隐藏",

        # 设置底部文字
        "settings_footnote_author": "Created by Triii Yukari · leaving my footprints with Nikki!",
        "settings_footnote_coffee": "https://buymeacoffee.com/triiitri",

        "edit_details_title": "编辑详情",
        "info_title": "信息",
        "id_label": "ID：—",
        "added_label": "添加时间：—",
        "added_prefix": "添加时间：",
        "delete_image_btn": "删除图片",

        "no_categories_title": "暂无分类",
        "no_categories_msg": "请先创建分类再添加图片。",
        "no_categories_snap_msg": "请先创建分类再使用截图功能。",
        "update_error_title": "更新错误",
        "delete_error_title": "删除错误",
        "import_error_title": "导入错误",
        "import_errors_title": "导入错误",
        "paste_error_title": "粘贴错误",
        "paste_no_image": "剪贴板中没有有效图片。",
        "snap_error_title": "截图错误",
        "snap_no_categories": "没有可用的分类来保存图片。",
        "snap_import_error": "截图导入错误",
        "validation_error_title": "验证错误",
        "validation_name_empty": "分类名称不能为空。",
        "validation_subname_empty": "子分类名称不能为空。",
        "validation_select_category": "请选择分类。",
        "validation_select_file": "请选择图片文件。",
        "validation_select_image_category": "请选择分类。",
        "validation_name_cannot_be_empty": "名称不能为空。",
        "confirm_delete_title": "删除{item_type}",
        "confirm_delete_msg": "确定要删除 '{item_name}' 吗？\n\n此操作无法撤销。",

        "rename_action": "重命名",
        "delete_action": "删除",

        "error_title": "错误",
        "error_create_category": "创建分类失败：{error}",
        "error_create_subcategory": "创建子分类失败：{error}",
        "error_rename": "重命名失败：{error}",
        "error_delete": "删除失败：{error}",
        "error_no_categories": "请先创建分类。",

        "copy_tooltip": "复制到剪贴板",
    },

    "ja": {
        "search_placeholder": "名前・カテゴリ・シェアコードで検索…",
        "sort_label": "並び替え：",
        "sort_newest": "新しい順",
        "sort_oldest": "古い順",
        "sort_name": "名前 A-Z",
        "add_image_btn": "+ 画像を追加",

        "add_category_btn": "+ カテゴリ",
        "add_subcategory_btn": "+ サブカテゴリ",
        "show_all_btn": "全画像を表示",

        "cancel": "キャンセル",
        "save": "保存",

        "add_category_title": "カテゴリを追加",
        "category_name_label": "カテゴリ名",
        "category_name_placeholder": "カテゴリ名を入力…",
        "create_category_btn": "カテゴリを作成",

        "add_subcategory_title": "サブカテゴリを追加",
        "parent_category_label": "カテゴリ",
        "subcategory_name_label": "サブカテゴリ名",
        "subcategory_name_placeholder": "サブカテゴリ名を入力…",
        "create_subcategory_btn": "サブカテゴリを作成",

        "add_image_title": "画像を追加",
        "edit_image_title": "画像を編集",
        "select_file_label": "ファイルを選択",
        "no_file_selected": "ファイル未選択",
        "browse_btn": "参照…",
        "display_name_label": "表示名（任意）",
        "display_name_label_required": "表示名",
        "display_name_placeholder": "表示名を入力…",
        "category_label": "カテゴリ",
        "subcategory_label": "サブカテゴリ",
        "none_option": "（なし）",
        "sharecode_label": "シェアコード（任意）",
        "sharecode_label_required": "シェアコード",
        "sharecode_placeholder": "シェアコードを入力…",
        "add_image_ok_btn": "画像を追加",
        "save_changes_btn": "変更を保存",

        "rename_category_title": "カテゴリ名を変更",
        "rename_subcategory_title": "サブカテゴリ名を変更",
        "new_name_label": "新しい名前",
        "rename_btn": "名前を変更",

        "snap_title": "スナップ撮影",
        "snap_initializing": "初期化中…",
        "snap_step": "ステップ {step} / 10",
        "snap_window_title": "スナップ実行中",

        "settings_title": "設定",
        "snap_mode_label": "スナップモード：",
        "snap_mode_album": "モード 1：アルバムに追加",
        "snap_mode_nikkibook": "モード 2：NikkiBook のみ保存",
        "capture_area_label": "スクリーンショット範囲（px）：",
        "capture_width_label": "幅",
        "capture_height_label": "高さ",
        "capture_offset_label": "左オフセット",
        "capture_default_hint": "空欄の場合は既定の 450 × 600 px、左オフセット 450 px を使用します。",
        "language_label": "表示言語：",
        "snap_visibility_label": "Snap（ベータ機能）：",
        "snap_visible": "表示",
        "snap_hidden": "非表示",

        # 設定のフッター
        "settings_footnote_author": "Created by Triii Yukari · leaving my footprints with Nikki!",
        "settings_footnote_coffee": "https://buymeacoffee.com/triiitri",

        "edit_details_title": "詳細を編集",
        "info_title": "情報",
        "id_label": "ID：—",
        "added_label": "追加日：—",
        "added_prefix": "追加日：",
        "delete_image_btn": "画像を削除",

        "no_categories_title": "カテゴリなし",
        "no_categories_msg": "画像を追加する前にカテゴリを作成してください。",
        "no_categories_snap_msg": "スナップを使用する前にカテゴリを作成してください。",
        "update_error_title": "更新エラー",
        "delete_error_title": "削除エラー",
        "import_error_title": "インポートエラー",
        "import_errors_title": "インポートエラー",
        "paste_error_title": "貼り付けエラー",
        "paste_no_image": "クリップボードに有効な画像がありません。",
        "snap_error_title": "スナップエラー",
        "snap_no_categories": "画像を保存できるカテゴリがありません。",
        "snap_import_error": "スナップインポートエラー",
        "validation_error_title": "入力エラー",
        "validation_name_empty": "カテゴリ名を入力してください。",
        "validation_subname_empty": "サブカテゴリ名を入力してください。",
        "validation_select_category": "親カテゴリを選択してください。",
        "validation_select_file": "画像ファイルを選択してください。",
        "validation_select_image_category": "カテゴリを選択してください。",
        "validation_name_cannot_be_empty": "名前を入力してください。",
        "confirm_delete_title": "{item_type}を削除",
        "confirm_delete_msg": "'{item_name}' を削除してもよろしいですか？\n\nこの操作は元に戻せません。",

        "rename_action": "名前を変更",
        "delete_action": "削除",

        "error_title": "エラー",
        "error_create_category": "カテゴリの作成に失敗しました：{error}",
        "error_create_subcategory": "サブカテゴリの作成に失敗しました：{error}",
        "error_rename": "名前の変更に失敗しました：{error}",
        "error_delete": "削除に失敗しました：{error}",
        "error_no_categories": "先にカテゴリを作成してください。",

        "copy_tooltip": "クリップボードにコピー",
    },
}

LANGUAGE_NAMES = {
    "en": "English",
    "zh": "中文",
    "ja": "日本語",
}


# ---------------------------------------------------------------------------
# Global language manager
# ---------------------------------------------------------------------------
def detect_system_language() -> str:
    """Return NikkiBook's supported language closest to the system locale."""
    system_language = QLocale.system().language()
    if system_language == QLocale.Language.Chinese:
        return "zh"
    if system_language == QLocale.Language.Japanese:
        return "ja"
    return "en"


class _LanguageManager(QObject):
    """Singleton that holds the active language and notifies listeners."""

    language_changed = pyqtSignal(str)  # emits new language code

    def __init__(self):
        super().__init__()
        self._settings = QSettings("NikkiBook", "App")
        saved_language = self._settings.value("language", None)
        if saved_language is None:
            self._lang = detect_system_language()
            self._settings.setValue("language", self._lang)
        else:
            self._lang = str(saved_language)
            if self._lang not in TRANSLATIONS:
                self._lang = "en"

    @property
    def language(self) -> str:
        return self._lang

    def set_language(self, lang: str):
        if lang not in TRANSLATIONS:
            return
        if lang == self._lang:
            return
        self._lang = lang
        self._settings.setValue("language", lang)
        self.language_changed.emit(lang)

    def t(self, key: str, **kwargs) -> str:
        """Return the translated string for the current language."""
        strings = TRANSLATIONS.get(self._lang, TRANSLATIONS["en"])
        text = strings.get(key, TRANSLATIONS["en"].get(key, key))
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, IndexError):
                pass
        return text


# Singleton instance
_manager: _LanguageManager | None = None


def get_manager() -> _LanguageManager:
    global _manager
    if _manager is None:
        _manager = _LanguageManager()
    return _manager


def t(key: str, **kwargs) -> str:
    """Shortcut: translate a key with the current language."""
    return get_manager().t(key, **kwargs)
