"""
Slooh Image Downloader - Windows Forms GUI
Main application window with DPI-aware auto-layout
"""

import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
clr.AddReference('System')

from System.Windows.Forms import (
    Application, Form, TableLayoutPanel, FlowLayoutPanel, Panel,
    Button, Label, TextBox, ProgressBar, ListBox, DataGridView,
    MenuStrip, ToolStripMenuItem, StatusStrip, ToolStripStatusLabel,
    SplitContainer, Orientation, DockStyle, AnchorStyles,
    FormBorderStyle, FormStartPosition, DialogResult, MessageBox,
    MessageBoxButtons, MessageBoxIcon, TabControl, TabPage,
    DataGridViewSelectionMode, DataGridViewAutoSizeColumnsMode,
    DataGridViewColumnSortMode, BorderStyle, AutoSizeMode, AutoScaleMode,
    ScrollBars, CheckBox, Padding, RowStyle, ColumnStyle, SizeType,
    FolderBrowserDialog, CheckedListBox, DateTimePicker
)
from System.Drawing import (
    Size, Point, Color, Font, FontStyle, SystemFonts, ContentAlignment
)
from System import EventArgs, Action, Threading
import System
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigurationManager, get_config
from logger import Logger, get_logger
from slooh_client import SloohClient
from download_manager import DownloadManager
from file_organizer import FileOrganizer
from batch_manager import BatchManager
from download_tracker import DownloadTracker
from report_generator import ReportGenerator


class SloohDownloaderForm(Form):
    """Main application form with DPI-aware layout"""
    
    def __init__(self):
        """Initialize the main form"""
        self.InitializeComponent()
        self.InitializeDownloader()
        
    def InitializeComponent(self):
        """Setup UI components with auto-layout"""
        # Form properties
        self.Text = "Slooh Image Downloader"
        self.Size = Size(1200, 800)
        self.MinimumSize = Size(800, 600)
        self.StartPosition = FormStartPosition.CenterScreen
        self.AutoScaleMode = AutoScaleMode.Font  # DPI-aware scaling
        
        # Create main layout (vertical split)
        self.main_layout = TableLayoutPanel()
        self.main_layout.Dock = DockStyle.Fill
        self.main_layout.RowCount = 3
        self.main_layout.ColumnCount = 1
        self.main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 50))  # Menu/toolbar
        self.main_layout.RowStyles.Add(RowStyle(SizeType.Percent, 100))  # Main content
        self.main_layout.RowStyles.Add(RowStyle(SizeType.Absolute, 30))  # Status bar
        
        # Add menu
        self.CreateMenu()
        
        # Create tab control for main content
        self.tabs = TabControl()
        self.tabs.Dock = DockStyle.Fill
        
        # Create tabs
        self.CreateDownloadTab()
        self.CreateHistoryTab()
        self.CreateConfigTab()
        self.CreateStatsTab()
        self.CreateAdvancedTab()
        
        self.main_layout.Controls.Add(self.tabs, 0, 1)
        
        # Create status bar
        self.CreateStatusBar()
        
        # Add main layout to form
        self.Controls.Add(self.main_layout)
        
        # Add Load event handler to adjust splitter after form is shown
        self.Load += self.OnFormLoad
        
    def OnFormLoad(self, sender, e):
        """Handle form load event - set splitter to 50% after form is shown"""
        if hasattr(self, 'main_split'):
            # Set horizontal splitter to 50% of the panel width
            self.main_split.SplitterDistance = self.main_split.Width // 2
        
    def CreateMenu(self):
        """Create menu bar"""
        menu = MenuStrip()
        menu.Dock = DockStyle.Top
        
        # File menu
        file_menu = ToolStripMenuItem("&File")
        file_menu.DropDownItems.Add("&Login", None, self.OnLogin)
        file_menu.DropDownItems.Add("&Logout", None, self.OnLogout)
        file_menu.DropDownItems.Add("-")  # Separator
        file_menu.DropDownItems.Add("E&xit", None, self.OnExit)
        menu.Items.Add(file_menu)
        
        # Downloads menu
        downloads_menu = ToolStripMenuItem("&Downloads")
        downloads_menu.DropDownItems.Add("&Start", None, self.OnStartDownload)
        downloads_menu.DropDownItems.Add("&Pause", None, self.OnPauseDownload)
        downloads_menu.DropDownItems.Add("&Stop", None, self.OnStopDownload)
        downloads_menu.DropDownItems.Add("-")
        downloads_menu.DropDownItems.Add("&Refresh Missions", None, self.OnRefreshMissions)
        menu.Items.Add(downloads_menu)
        
        # Tools menu
        tools_menu = ToolStripMenuItem("&Tools")
        
        # Export submenu
        export_menu = ToolStripMenuItem("&Export Reports")
        export_menu.DropDownItems.Add("Export to &CSV", None, self.OnExportCSV)
        export_menu.DropDownItems.Add("Export to &HTML", None, self.OnExportHTML)
        export_menu.DropDownItems.Add("Export &Statistics", None, self.OnExportStatistics)
        tools_menu.DropDownItems.Add(export_menu)
        
        tools_menu.DropDownItems.Add("-")
        tools_menu.DropDownItems.Add("&Verify Downloads", None, self.OnVerifyDownloads)
        tools_menu.DropDownItems.Add("Find &Orphaned Files", None, self.OnFindOrphaned)
        tools_menu.DropDownItems.Add("Clean Missing from Tracker", None, self.OnCleanMissing)
        tools_menu.DropDownItems.Add("-")
        tools_menu.DropDownItems.Add("Clean Old &Sessions", None, self.OnCleanSessions)
        tools_menu.DropDownItems.Add("&Backup Tracker", None, self.OnBackupTracker)
        menu.Items.Add(tools_menu)
        
        # Help menu
        help_menu = ToolStripMenuItem("&Help")
        help_menu.DropDownItems.Add("&About", None, self.OnAbout)
        menu.Items.Add(help_menu)
        
        self.main_layout.Controls.Add(menu, 0, 0)
        self.main_menu = menu
        
    def CreateDownloadTab(self):
        """Create download control tab"""
        tab = TabPage("Download")
        
        # Main vertical split container (top: controls, bottom: progress)
        split = SplitContainer()
        split.Dock = DockStyle.Fill
        split.Orientation = Orientation.Horizontal
        split.SplitterDistance = 450
        
        # Create horizontal split for left/right panels in top section
        main_split = SplitContainer()
        main_split.Orientation = Orientation.Vertical
        main_split.Dock = DockStyle.Fill
        # Set to 50% width by using SplitterDistance based on form width
        # Will be set after form is shown, for now use approximate value
        main_split.SplitterDistance = 500
        
        # LEFT PANEL - Credentials and Controls
        left_panel = TableLayoutPanel()
        left_panel.Dock = DockStyle.Fill
        left_panel.ColumnCount = 2
        left_panel.Padding = Padding(10)
        left_panel.AutoScroll = True
        left_panel.ColumnStyles.Add(ColumnStyle(SizeType.AutoSize))  # Labels
        left_panel.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100))  # Controls
        
        row = 0
        
        # Credentials section
        lbl_creds = Label()
        lbl_creds.Text = "Login Credentials"
        lbl_creds.Font = Font(SystemFonts.DefaultFont.FontFamily, 9.0, FontStyle.Bold)
        lbl_creds.AutoSize = True
        left_panel.Controls.Add(lbl_creds, 0, row)
        left_panel.SetColumnSpan(lbl_creds, 2)
        
        # Username
        row += 1
        lbl_username = Label()
        lbl_username.Text = "Username:"
        lbl_username.Anchor = AnchorStyles.Left
        lbl_username.AutoSize = True
        left_panel.Controls.Add(lbl_username, 0, row)
        
        self.txt_username = TextBox()
        self.txt_username.Anchor = AnchorStyles.Left | AnchorStyles.Right
        left_panel.Controls.Add(self.txt_username, 1, row)
        
        # Password
        row += 1
        lbl_password = Label()
        lbl_password.Text = "Password:"
        lbl_password.Anchor = AnchorStyles.Left
        lbl_password.AutoSize = True
        left_panel.Controls.Add(lbl_password, 0, row)
        
        self.txt_password = TextBox()
        self.txt_password.Anchor = AnchorStyles.Left | AnchorStyles.Right
        self.txt_password.UseSystemPasswordChar = True
        left_panel.Controls.Add(self.txt_password, 1, row)
        
        # Login button
        row += 1
        self.btn_login = Button()
        self.btn_login.Text = "Login"
        self.btn_login.Width = 100
        self.btn_login.Anchor = AnchorStyles.Left
        self.btn_login.Click += self.OnLogin
        left_panel.Controls.Add(self.btn_login, 1, row)
        
        # Download settings section
        row += 1
        lbl_settings = Label()
        lbl_settings.Text = "Download Settings"
        lbl_settings.Font = Font(SystemFonts.DefaultFont.FontFamily, 9.0, FontStyle.Bold)
        lbl_settings.AutoSize = True
        left_panel.Controls.Add(lbl_settings, 0, row)
        left_panel.SetColumnSpan(lbl_settings, 2)
        
        # Mission selection
        row += 1
        lbl_mission = Label()
        lbl_mission.Text = "Mission ID:"
        lbl_mission.Anchor = AnchorStyles.Left
        lbl_mission.AutoSize = True
        left_panel.Controls.Add(lbl_mission, 0, row)
        
        mission_panel = FlowLayoutPanel()
        mission_panel.AutoSize = True
        
        self.txt_mission = TextBox()
        self.txt_mission.Width = 100
        mission_panel.Controls.Add(self.txt_mission)
        
        self.chk_all_missions = CheckBox()
        self.chk_all_missions.Text = "All Missions"
        self.chk_all_missions.AutoSize = True
        mission_panel.Controls.Add(self.chk_all_missions)
        
        left_panel.Controls.Add(mission_panel, 1, row)
        
        # Max count
        row += 1
        lbl_max = Label()
        lbl_max.Text = "Max Images:"
        lbl_max.Anchor = AnchorStyles.Left
        lbl_max.AutoSize = True
        left_panel.Controls.Add(lbl_max, 0, row)
        
        self.txt_max_count = TextBox()
        self.txt_max_count.Text = "50"
        self.txt_max_count.Width = 100
        self.txt_max_count.Anchor = AnchorStyles.Left
        left_panel.Controls.Add(self.txt_max_count, 1, row)
        
        # Max scan count
        row += 1
        lbl_max_scan = Label()
        lbl_max_scan.Text = "Max Scan:"
        lbl_max_scan.Anchor = AnchorStyles.Left
        lbl_max_scan.AutoSize = True
        left_panel.Controls.Add(lbl_max_scan, 0, row)
        
        max_scan_panel = FlowLayoutPanel()
        max_scan_panel.AutoSize = True
        max_scan_panel.Anchor = AnchorStyles.Left
        
        self.txt_max_scan = TextBox()
        self.txt_max_scan.Text = "0"
        self.txt_max_scan.Width = 80
        max_scan_panel.Controls.Add(self.txt_max_scan)
        
        lbl_scan_hint = Label()
        lbl_scan_hint.Text = "(0 = all)"
        lbl_scan_hint.AutoSize = True
        lbl_scan_hint.Anchor = AnchorStyles.Left
        lbl_scan_hint.TextAlign = ContentAlignment.MiddleLeft
        lbl_scan_hint.Padding = Padding(5, 3, 0, 0)  # Add padding for vertical alignment
        lbl_scan_hint.ForeColor = System.Drawing.Color.Gray
        max_scan_panel.Controls.Add(lbl_scan_hint)
        
        left_panel.Controls.Add(max_scan_panel, 1, row)
        
        # Start Image Number
        row += 1
        lbl_start_image = Label()
        lbl_start_image.Text = "Start Image #:"
        lbl_start_image.Anchor = AnchorStyles.Left
        lbl_start_image.AutoSize = True
        left_panel.Controls.Add(lbl_start_image, 0, row)
        
        start_image_panel = FlowLayoutPanel()
        start_image_panel.AutoSize = True
        start_image_panel.Anchor = AnchorStyles.Left
        
        self.txt_start_image = TextBox()
        self.txt_start_image.Text = "1"
        self.txt_start_image.Width = 80
        self.txt_start_image.TextChanged += self.OnStartImageChanged
        start_image_panel.Controls.Add(self.txt_start_image)
        
        self.lbl_start_image_hint = Label()
        self.lbl_start_image_hint.Text = "(1 = most recent)"
        self.lbl_start_image_hint.AutoSize = True
        self.lbl_start_image_hint.Anchor = AnchorStyles.Left
        self.lbl_start_image_hint.TextAlign = ContentAlignment.MiddleLeft
        self.lbl_start_image_hint.Padding = Padding(5, 3, 0, 0)
        self.lbl_start_image_hint.ForeColor = System.Drawing.Color.Gray
        start_image_panel.Controls.Add(self.lbl_start_image_hint)
        
        left_panel.Controls.Add(start_image_panel, 1, row)
        
        # Options section
        row += 1
        lbl_options = Label()
        lbl_options.Text = "Options"
        lbl_options.Font = Font(SystemFonts.DefaultFont.FontFamily, 9.0, FontStyle.Bold)
        lbl_options.AutoSize = True
        left_panel.Controls.Add(lbl_options, 0, row)
        left_panel.SetColumnSpan(lbl_options, 2)
        
        # Debug Level checkbox
        row += 1
        self.chk_debug_logging = CheckBox()
        self.chk_debug_logging.Text = "Enable Debug Logging"
        self.chk_debug_logging.AutoSize = True
        self.chk_debug_logging.CheckedChanged += self.OnDebugLevelChanged
        left_panel.SetColumnSpan(self.chk_debug_logging, 2)
        left_panel.Controls.Add(self.chk_debug_logging, 0, row)
        
        # Dry-run checkbox
        row += 1
        self.chk_dry_run = CheckBox()
        self.chk_dry_run.Text = "Dry Run (Preview Only)"
        self.chk_dry_run.AutoSize = True
        left_panel.SetColumnSpan(self.chk_dry_run, 2)
        left_panel.Controls.Add(self.chk_dry_run, 0, row)
        
        # Force redownload checkbox
        row += 1
        self.chk_force_redownload = CheckBox()
        self.chk_force_redownload.Text = "Force Redownload (Ignore Tracker)"
        self.chk_force_redownload.AutoSize = True
        left_panel.SetColumnSpan(self.chk_force_redownload, 2)
        left_panel.Controls.Add(self.chk_force_redownload, 0, row)
        
        # Download buttons
        row += 1
        btn_panel = FlowLayoutPanel()
        btn_panel.AutoSize = True
        
        self.btn_start = Button()
        self.btn_start.Text = "Start Download"
        self.btn_start.Width = 120
        self.btn_start.Enabled = False
        self.btn_start.Click += self.OnStartDownload
        btn_panel.Controls.Add(self.btn_start)
        
        self.btn_pause = Button()
        self.btn_pause.Text = "Pause"
        self.btn_pause.Width = 80
        self.btn_pause.Enabled = False
        self.btn_pause.Click += self.OnPauseDownload
        btn_panel.Controls.Add(self.btn_pause)
        
        self.btn_stop = Button()
        self.btn_stop.Text = "Stop"
        self.btn_stop.Width = 80
        self.btn_stop.Enabled = False
        self.btn_stop.Click += self.OnStopDownload
        btn_panel.Controls.Add(self.btn_stop)
        
        left_panel.Controls.Add(btn_panel, 0, row)
        left_panel.SetColumnSpan(btn_panel, 2)
        
        # Status label
        row += 1
        self.lbl_status = Label()
        self.lbl_status.Text = "Not logged in"
        self.lbl_status.Anchor = AnchorStyles.Left | AnchorStyles.Right
        self.lbl_status.AutoSize = True
        left_panel.SetColumnSpan(self.lbl_status, 2)
        left_panel.Controls.Add(self.lbl_status, 0, row)
        
        main_split.Panel1.Controls.Add(left_panel)
        
        # RIGHT PANEL - Filters
        right_panel = TableLayoutPanel()
        right_panel.Dock = DockStyle.Fill
        right_panel.ColumnCount = 2
        right_panel.Padding = Padding(10)
        right_panel.AutoScroll = True
        right_panel.ColumnStyles.Add(ColumnStyle(SizeType.AutoSize))  # Labels
        right_panel.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100))  # Controls
        
        row = 0
        
        # Filters section
        lbl_filters = Label()
        lbl_filters.Text = "Filters (optional)"
        lbl_filters.Font = Font(SystemFonts.DefaultFont.FontFamily, 9.0, FontStyle.Bold)
        lbl_filters.AutoSize = True
        right_panel.SetColumnSpan(lbl_filters, 2)
        right_panel.Controls.Add(lbl_filters, 0, row)
        
        # Telescope filter
        row += 1
        lbl_telescope = Label()
        lbl_telescope.Text = "Telescopes:"
        lbl_telescope.Anchor = AnchorStyles.Left | AnchorStyles.Top
        lbl_telescope.AutoSize = True
        right_panel.Controls.Add(lbl_telescope, 0, row)
        
        self.lst_filter_telescope = CheckedListBox()
        self.lst_filter_telescope.Anchor = AnchorStyles.Left | AnchorStyles.Right
        self.lst_filter_telescope.Height = 120
        self.lst_filter_telescope.CheckOnClick = True
        self.lst_filter_telescope.Items.Add("Chile One")
        self.lst_filter_telescope.Items.Add("Chile Two")
        self.lst_filter_telescope.Items.Add("Chile Three")
        self.lst_filter_telescope.Items.Add("Canary One")
        self.lst_filter_telescope.Items.Add("Canary Two")
        self.lst_filter_telescope.Items.Add("Canary Three")
        self.lst_filter_telescope.Items.Add("Canary Four")
        self.lst_filter_telescope.Items.Add("Canary Five")
        self.lst_filter_telescope.Items.Add("Australia One")
        right_panel.Controls.Add(self.lst_filter_telescope, 1, row)
        
        # Object filter
        row += 1
        lbl_object = Label()
        lbl_object.Text = "Object:"
        lbl_object.Anchor = AnchorStyles.Left
        lbl_object.AutoSize = True
        right_panel.Controls.Add(lbl_object, 0, row)
        
        self.txt_filter_object = TextBox()
        self.txt_filter_object.Anchor = AnchorStyles.Left | AnchorStyles.Right
        right_panel.Controls.Add(self.txt_filter_object, 1, row)
        
        # Picture Type filter
        row += 1
        lbl_picture_type = Label()
        lbl_picture_type.Text = "Picture Types:"
        lbl_picture_type.Anchor = AnchorStyles.Left | AnchorStyles.Top
        lbl_picture_type.AutoSize = True
        right_panel.Controls.Add(lbl_picture_type, 0, row)
        
        self.lst_picture_types = CheckedListBox()
        self.lst_picture_types.Anchor = AnchorStyles.Left | AnchorStyles.Right
        self.lst_picture_types.Height = 60
        self.lst_picture_types.CheckOnClick = True
        self.lst_picture_types.Items.Add("PNG")
        self.lst_picture_types.Items.Add("JPEG")
        self.lst_picture_types.Items.Add("FITS")
        for i in range(self.lst_picture_types.Items.Count):
            self.lst_picture_types.SetItemChecked(i, True)
        right_panel.Controls.Add(self.lst_picture_types, 1, row)
        
        # Date Range section
        row += 1
        lbl_date_section = Label()
        lbl_date_section.Text = "Date Range"
        lbl_date_section.Font = Font(SystemFonts.DefaultFont.FontFamily, 9.0, FontStyle.Bold)
        lbl_date_section.AutoSize = True
        right_panel.SetColumnSpan(lbl_date_section, 2)
        right_panel.Controls.Add(lbl_date_section, 0, row)
        
        # Start date
        row += 1
        lbl_start_date = Label()
        lbl_start_date.Text = "Start Date:"
        lbl_start_date.Anchor = AnchorStyles.Left | AnchorStyles.Top
        lbl_start_date.AutoSize = True
        right_panel.Controls.Add(lbl_start_date, 0, row)
        
        date_start_panel = FlowLayoutPanel()
        date_start_panel.AutoSize = True
        
        self.chk_use_start_date = CheckBox()
        self.chk_use_start_date.Text = "Enable"
        self.chk_use_start_date.AutoSize = True
        self.chk_use_start_date.Checked = False
        date_start_panel.Controls.Add(self.chk_use_start_date)
        
        self.dtp_start_date = DateTimePicker()
        self.dtp_start_date.Format = System.Windows.Forms.DateTimePickerFormat.Short
        self.dtp_start_date.Width = 120
        date_start_panel.Controls.Add(self.dtp_start_date)
        
        right_panel.Controls.Add(date_start_panel, 1, row)
        
        # End date
        row += 1
        lbl_end_date = Label()
        lbl_end_date.Text = "End Date:"
        lbl_end_date.Anchor = AnchorStyles.Left | AnchorStyles.Top
        lbl_end_date.AutoSize = True
        right_panel.Controls.Add(lbl_end_date, 0, row)
        
        date_end_panel = FlowLayoutPanel()
        date_end_panel.AutoSize = True
        
        self.chk_use_end_date = CheckBox()
        self.chk_use_end_date.Text = "Enable"
        self.chk_use_end_date.AutoSize = True
        self.chk_use_end_date.Checked = False
        date_end_panel.Controls.Add(self.chk_use_end_date)
        
        self.dtp_end_date = DateTimePicker()
        self.dtp_end_date.Format = System.Windows.Forms.DateTimePickerFormat.Short
        self.dtp_end_date.Width = 120
        date_end_panel.Controls.Add(self.dtp_end_date)
        
        right_panel.Controls.Add(date_end_panel, 1, row)
        
        main_split.Panel2.Controls.Add(right_panel)
        
        # Store reference to main_split so we can adjust it on form load
        self.main_split = main_split
        
        # Add main split to top of vertical split
        split.Panel1.Controls.Add(main_split)
        
        # Bottom panel - Progress display
        progress_panel = TableLayoutPanel()
        progress_panel.Dock = DockStyle.Fill
        progress_panel.RowCount = 4
        progress_panel.ColumnCount = 1
        progress_panel.Padding = Padding(10)
        
        # Row 0-2: AutoSize for labels and progress bar
        # Row 3: Percent for log to fill remaining space
        progress_panel.RowStyles.Add(RowStyle(SizeType.AutoSize))  # Overall Progress label
        progress_panel.RowStyles.Add(RowStyle(SizeType.AutoSize))  # Progress bar
        progress_panel.RowStyles.Add(RowStyle(SizeType.AutoSize))  # Current file label
        progress_panel.RowStyles.Add(RowStyle(SizeType.Percent, 100))  # Log fills remaining
        progress_panel.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100))
        
        # Overall progress
        lbl_overall = Label()
        lbl_overall.Text = "Overall Progress:"
        lbl_overall.AutoSize = True
        progress_panel.Controls.Add(lbl_overall, 0, 0)
        
        self.progress_overall = ProgressBar()
        self.progress_overall.Dock = DockStyle.Fill
        self.progress_overall.Height = 30
        progress_panel.Controls.Add(self.progress_overall, 0, 1)
        
        # Current file
        self.lbl_current_file = Label()
        self.lbl_current_file.Text = "Ready"
        self.lbl_current_file.AutoSize = True
        progress_panel.Controls.Add(self.lbl_current_file, 0, 2)
        
        # Progress log
        self.txt_log = TextBox()
        self.txt_log.Multiline = True
        self.txt_log.ScrollBars = ScrollBars.Both
        self.txt_log.ReadOnly = True
        self.txt_log.Dock = DockStyle.Fill
        # Don't set explicit Height - let TableLayoutPanel control it via Percent sizing
        progress_panel.Controls.Add(self.txt_log, 0, 3)
        
        split.Panel2.Controls.Add(progress_panel)
        
        tab.Controls.Add(split)
        self.tabs.TabPages.Add(tab)
        
        # Store references
        self.download_tab = tab
        
    def CreateHistoryTab(self):
        """Create download history browser tab"""
        tab = TabPage("History")
        
        # Create grid for history
        self.grid_history = DataGridView()
        self.grid_history.Dock = DockStyle.Fill
        self.grid_history.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill
        self.grid_history.SelectionMode = DataGridViewSelectionMode.FullRowSelect
        self.grid_history.MultiSelect = False
        self.grid_history.ReadOnly = True
        self.grid_history.AllowUserToAddRows = False
        
        # Add columns
        self.grid_history.Columns.Add("image_id", "Image ID")
        self.grid_history.Columns.Add("title", "Title")
        self.grid_history.Columns.Add("timestamp", "Date/Time")
        self.grid_history.Columns.Add("telescope", "Telescope")
        self.grid_history.Columns.Add("status", "Status")
        self.grid_history.Columns.Add("file_path", "File Path")
        
        tab.Controls.Add(self.grid_history)
        self.tabs.TabPages.Add(tab)
        
    def CreateConfigTab(self):
        """Create configuration editor tab"""
        tab = TabPage("Configuration")
        
        config_panel = TableLayoutPanel()
        config_panel.Dock = DockStyle.Fill
        config_panel.RowCount = 11
        config_panel.ColumnCount = 3
        config_panel.Padding = Padding(10)
        
        for i in range(11):
            config_panel.RowStyles.Add(RowStyle(SizeType.AutoSize))
        config_panel.ColumnStyles.Add(ColumnStyle(SizeType.AutoSize))
        config_panel.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100))
        config_panel.ColumnStyles.Add(ColumnStyle(SizeType.AutoSize))
        
        row = 0
        
        # Download directory
        lbl_dir = Label()
        lbl_dir.Text = "Download Directory:"
        lbl_dir.AutoSize = True
        config_panel.Controls.Add(lbl_dir, 0, row)
        
        self.txt_download_dir = TextBox()
        self.txt_download_dir.Anchor = AnchorStyles.Left | AnchorStyles.Right
        config_panel.Controls.Add(self.txt_download_dir, 1, row)
        
        self.btn_browse_folder = Button()
        self.btn_browse_folder.Text = "Browse..."
        self.btn_browse_folder.Width = 80
        self.btn_browse_folder.Click += self.OnBrowseFolder
        config_panel.Controls.Add(self.btn_browse_folder, 2, row)
        
        # Max concurrent downloads
        row += 1
        lbl_concurrent = Label()
        lbl_concurrent.Text = "Max Concurrent:"
        lbl_concurrent.AutoSize = True
        config_panel.Controls.Add(lbl_concurrent, 0, row)
        
        self.txt_max_concurrent = TextBox()
        self.txt_max_concurrent.Width = 100
        config_panel.Controls.Add(self.txt_max_concurrent, 1, row)
        
        # Rate limit
        row += 1
        lbl_rate = Label()
        lbl_rate.Text = "Rate Limit (req/min):"
        lbl_rate.AutoSize = True
        config_panel.Controls.Add(lbl_rate, 0, row)
        
        self.txt_rate_limit = TextBox()
        self.txt_rate_limit.Width = 100
        config_panel.Controls.Add(self.txt_rate_limit, 1, row)
        
        # Max retries
        row += 1
        lbl_retries = Label()
        lbl_retries.Text = "Max Retries:"
        lbl_retries.AutoSize = True
        config_panel.Controls.Add(lbl_retries, 0, row)
        
        self.txt_max_retries = TextBox()
        self.txt_max_retries.Width = 100
        config_panel.Controls.Add(self.txt_max_retries, 1, row)
        
        # File organization template
        row += 1
        lbl_template = Label()
        lbl_template.Text = "File Organization:"
        lbl_template.AutoSize = True
        config_panel.Controls.Add(lbl_template, 0, row)
        
        self.txt_template = TextBox()
        self.txt_template.Anchor = AnchorStyles.Left | AnchorStyles.Right
        config_panel.SetColumnSpan(self.txt_template, 2)
        config_panel.Controls.Add(self.txt_template, 1, row)
        
        # Template help
        row += 1
        lbl_help = Label()
        lbl_help.Text = "Available variables: {object}, {telescope}, {format}, {date}, {year}, {month}"
        lbl_help.AutoSize = True
        lbl_help.ForeColor = System.Drawing.Color.Gray
        config_panel.SetColumnSpan(lbl_help, 3)
        config_panel.Controls.Add(lbl_help, 0, row)
        
        # Save button
        row += 1
        self.btn_save_config = Button()
        self.btn_save_config.Text = "Save Configuration"
        self.btn_save_config.Width = 150
        self.btn_save_config.Click += self.OnSaveConfig
        config_panel.Controls.Add(self.btn_save_config, 1, row)
        
        tab.Controls.Add(config_panel)
        self.tabs.TabPages.Add(tab)
        
    def CreateStatsTab(self):
        """Create statistics dashboard tab"""
        tab = TabPage("Statistics")
        
        stats_panel = TableLayoutPanel()
        stats_panel.Dock = DockStyle.Fill
        stats_panel.RowCount = 8
        stats_panel.ColumnCount = 2
        stats_panel.Padding = Padding(10)
        
        for i in range(8):
            stats_panel.RowStyles.Add(RowStyle(SizeType.AutoSize))
        stats_panel.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 50))
        stats_panel.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 50))
        
        # Title
        lbl_title = Label()
        lbl_title.Text = "Download Statistics"
        lbl_title.Font = Font(SystemFonts.DefaultFont.FontFamily, 14.0, FontStyle.Bold)
        lbl_title.AutoSize = True
        stats_panel.SetColumnSpan(lbl_title, 2)
        stats_panel.Controls.Add(lbl_title, 0, 0)
        
        row = 1
        
        # Total downloads
        self.AddStatLabel(stats_panel, "Total Downloads:", row)
        self.lbl_total_downloads = self.AddStatValue(stats_panel, "0", row)
        
        # Successful
        row += 1
        self.AddStatLabel(stats_panel, "Successful:", row)
        self.lbl_successful = self.AddStatValue(stats_panel, "0", row)
        
        # Failed
        row += 1
        self.AddStatLabel(stats_panel, "Failed:", row)
        self.lbl_failed = self.AddStatValue(stats_panel, "0", row)
        
        # Total size
        row += 1
        self.AddStatLabel(stats_panel, "Total Size:", row)
        self.lbl_total_size = self.AddStatValue(stats_panel, "0 MB", row)
        
        # Average speed
        row += 1
        self.AddStatLabel(stats_panel, "Average Speed:", row)
        self.lbl_avg_speed = self.AddStatValue(stats_panel, "0 KB/s", row)
        
        # Session stats
        row += 1
        lbl_session = Label()
        lbl_session.Text = "Current Session"
        lbl_session.Font = Font(SystemFonts.DefaultFont.FontFamily, 12.0, FontStyle.Bold)
        lbl_session.AutoSize = True
        stats_panel.SetColumnSpan(lbl_session, 2)
        stats_panel.Controls.Add(lbl_session, 0, row)
        
        # Session downloads
        row += 1
        self.AddStatLabel(stats_panel, "Session Downloads:", row)
        self.lbl_session_downloads = self.AddStatValue(stats_panel, "0", row)
        
        tab.Controls.Add(stats_panel)
        self.tabs.TabPages.Add(tab)
    
    def CreateAdvancedTab(self):
        """Create advanced options tab"""
        tab = TabPage("Advanced")
        
        advanced_panel = TableLayoutPanel()
        advanced_panel.Dock = DockStyle.Fill
        advanced_panel.RowCount = 15
        advanced_panel.ColumnCount = 3
        advanced_panel.Padding = Padding(10)
        
        for i in range(15):
            advanced_panel.RowStyles.Add(RowStyle(SizeType.AutoSize))
        advanced_panel.ColumnStyles.Add(ColumnStyle(SizeType.AutoSize))
        advanced_panel.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100))
        advanced_panel.ColumnStyles.Add(ColumnStyle(SizeType.AutoSize))
        
        row = 0
        
        # Title
        lbl_title = Label()
        lbl_title.Text = "Advanced Download Options"
        lbl_title.Font = Font(SystemFonts.DefaultFont.FontFamily, 12.0, FontStyle.Bold)
        lbl_title.AutoSize = True
        advanced_panel.SetColumnSpan(lbl_title, 3)
        advanced_panel.Controls.Add(lbl_title, 0, row)
        
        # Maintenance Section
        row += 1
        lbl_maint_section = Label()
        lbl_maint_section.Text = "Maintenance Tools"
        lbl_maint_section.Font = Font(SystemFonts.DefaultFont.FontFamily, 10.0, FontStyle.Bold)
        lbl_maint_section.AutoSize = True
        advanced_panel.SetColumnSpan(lbl_maint_section, 3)
        advanced_panel.Controls.Add(lbl_maint_section, 0, row)
        
        # Verify button
        row += 1
        btn_verify = Button()
        btn_verify.Text = "Verify All Downloads"
        btn_verify.Width = 180
        btn_verify.Click += self.OnVerifyDownloads
        advanced_panel.Controls.Add(btn_verify, 1, row)
        
        # Find orphaned button
        row += 1
        btn_orphaned = Button()
        btn_orphaned.Text = "Find Orphaned Files"
        btn_orphaned.Width = 180
        btn_orphaned.Click += self.OnFindOrphaned
        advanced_panel.Controls.Add(btn_orphaned, 1, row)
        
        # Clean missing button
        row += 1
        btn_clean_missing = Button()
        btn_clean_missing.Text = "Clean Missing from Tracker"
        btn_clean_missing.Width = 180
        btn_clean_missing.Click += self.OnCleanMissing
        advanced_panel.Controls.Add(btn_clean_missing, 1, row)
        
        # Clean sessions button
        row += 1
        btn_clean_sessions = Button()
        btn_clean_sessions.Text = "Clean Old Sessions"
        btn_clean_sessions.Width = 180
        btn_clean_sessions.Click += self.OnCleanSessions
        advanced_panel.Controls.Add(btn_clean_sessions, 1, row)
        
        # Backup button
        row += 1
        btn_backup = Button()
        btn_backup.Text = "Backup Tracker"
        btn_backup.Width = 180
        btn_backup.Click += self.OnBackupTracker
        advanced_panel.Controls.Add(btn_backup, 1, row)
        
        # Export Section
        row += 1
        lbl_export_section = Label()
        lbl_export_section.Text = "Export Reports"
        lbl_export_section.Font = Font(SystemFonts.DefaultFont.FontFamily, 10.0, FontStyle.Bold)
        lbl_export_section.AutoSize = True
        advanced_panel.SetColumnSpan(lbl_export_section, 3)
        advanced_panel.Controls.Add(lbl_export_section, 0, row)
        
        # Export CSV button
        row += 1
        btn_export_csv = Button()
        btn_export_csv.Text = "Export to CSV"
        btn_export_csv.Width = 180
        btn_export_csv.Click += self.OnExportCSV
        advanced_panel.Controls.Add(btn_export_csv, 1, row)
        
        # Export HTML button
        row += 1
        btn_export_html = Button()
        btn_export_html.Text = "Export to HTML"
        btn_export_html.Width = 180
        btn_export_html.Click += self.OnExportHTML
        advanced_panel.Controls.Add(btn_export_html, 1, row)
        
        # Export Statistics button
        row += 1
        btn_export_stats = Button()
        btn_export_stats.Text = "Export Statistics Report"
        btn_export_stats.Width = 180
        btn_export_stats.Click += self.OnExportStatistics
        advanced_panel.Controls.Add(btn_export_stats, 1, row)
        
        tab.Controls.Add(advanced_panel)
        self.tabs.TabPages.Add(tab)
        
    def AddStatLabel(self, panel, text, row):
        """Add a statistic label"""
        lbl = Label()
        lbl.Text = text
        lbl.AutoSize = True
        lbl.Anchor = AnchorStyles.Left
        panel.Controls.Add(lbl, 0, row)
        return lbl
        
    def AddStatValue(self, panel, text, row):
        """Add a statistic value label"""
        lbl = Label()
        lbl.Text = text
        lbl.AutoSize = True
        lbl.Anchor = AnchorStyles.Right
        lbl.Font = Font(SystemFonts.DefaultFont.FontFamily, 10.0, FontStyle.Bold)
        panel.Controls.Add(lbl, 1, row)
        return lbl
        
    def CreateStatusBar(self):
        """Create status bar"""
        status = StatusStrip()
        status.Dock = DockStyle.Bottom
        
        self.status_label = ToolStripStatusLabel()
        self.status_label.Text = "Ready"
        self.status_label.Spring = True
        self.status_label.TextAlign = ContentAlignment.MiddleLeft
        status.Items.Add(self.status_label)
        
        self.main_layout.Controls.Add(status, 0, 2)
        
    def InitializeDownloader(self):
        """Initialize downloader components"""
        try:
            self.config = get_config()
            self.logger = get_logger('SloohDownloader', self.config)
            
            # Register GUI callback to receive log messages
            def log_to_gui(level, message):
                # Only show INFO and above in GUI
                if level >= Logger.INFO:
                    self.LogMessage(message)
            
            self.logger.add_callback(log_to_gui)
            
            self.client = None
            # Store manager references so pause/stop buttons can access them
            self.download_manager = None
            self.batch_manager = None
            self.is_downloading = False
            self.is_paused = False
            
            # Load saved credentials if available
            username = self.config.get('credentials.username')
            if username:
                self.txt_username.Text = username
            
            password = self.config.get('credentials.password')
            if password:
                self.txt_password.Text = password
                
            # Load configuration into UI
            self.LoadConfiguration()
            
            # Load existing history and statistics
            self.LoadHistory()
            self.LoadStatistics()
            
            # Auto-check "All Missions"
            self.chk_all_missions.Checked = True
            
            # Auto-login if credentials are saved
            if username and password:
                self.LogMessage("Auto-login with saved credentials...")
                Threading.Thread(Threading.ThreadStart(self.AutoLogin)).Start()
            
            self.LogMessage("Application initialized")
        except Exception as e:
            MessageBox.Show(
                "Failed to initialize: {0}".format(str(e)),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            
    def LoadConfiguration(self):
        """Load configuration into UI"""
        try:
            # Load credentials
            username = self.config.get('credentials.username')
            password = self.config.get('credentials.password')
            if username:
                self.txt_username.Text = username
            if password:
                self.txt_password.Text = password
                
            # Load download settings with actual defaults
            base_path = self.config.get('folders.base_path', 'SloohImages')
            if not os.path.isabs(base_path):
                base_path = os.path.abspath(base_path)
            self.txt_download_dir.Text = base_path
            
            self.txt_max_concurrent.Text = str(self.config.get('download.threads', 4))
            self.txt_rate_limit.Text = str(self.config.get('download.rate_limit', 30))
            self.txt_max_retries.Text = str(self.config.get('download.max_retries', 3))
            self.txt_template.Text = self.config.get('folders.template', '{object}/{telescope}/{format}')
        except Exception as e:
            self.LogMessage("Error loading configuration: {0}".format(str(e)))
            
    # Event handlers
    def OnLogin(self, sender, e):
        """Handle login button click"""
        try:
            username = self.txt_username.Text
            password = self.txt_password.Text
            
            if not username or not password:
                MessageBox.Show(
                    "Please enter username and password",
                    "Login",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                )
                return
                
            self.lbl_status.Text = "Logging in..."
            self.btn_login.Enabled = False
            Application.DoEvents()
            
            # Create client and login
            base_url = self.config.get('slooh.base_url', 'https://app.slooh.com')
            self.client = SloohClient(base_url, self.logger)
            self.client.get_session_token()
            
            user_data = self.client.login(username, password)
            if user_data:
                display_name = user_data.get('displayName', username)
                self.lbl_status.Text = "Logged in as {0}".format(display_name)
                self.btn_start.Enabled = True
                self.LogMessage("Successfully logged in as {0}".format(display_name))
                
                # Save credentials (including password)
                self.config.set('credentials.username', username)
                self.config.set('credentials.password', password)
                self.config.save()
            else:
                self.lbl_status.Text = "Login failed"
                MessageBox.Show(
                    "Login failed. Please check credentials.",
                    "Login Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                )
                self.btn_login.Enabled = True
                
        except Exception as ex:
            self.lbl_status.Text = "Login error"
            MessageBox.Show(
                "Login error: {0}".format(str(ex)),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            self.btn_login.Enabled = True
            
    def OnLogout(self, sender, e):
        """Handle logout"""
        self.client = None
        self.lbl_status.Text = "Logged out"
        self.btn_login.Enabled = True
        self.btn_start.Enabled = False
        self.LogMessage("Logged out")
        
    def OnStartDownload(self, sender, e):
        """Handle start download button"""
        if self.is_downloading:
            if self.is_paused:
                # Resume
                self.is_paused = False
                self.btn_pause.Text = "Pause"
                self.LogMessage("Resuming download...")
            return
            
        try:
            # Reset control flags for new session
            self.is_downloading = True
            self.is_paused = False
            # Validate inputs
            mission_id = None
            if not self.chk_all_missions.Checked:
                try:
                    mission_id = int(self.txt_mission.Text)
                except:
                    MessageBox.Show(
                        "Please enter a valid mission ID",
                        "Input Error",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Warning
                    )
                    return
                    
            max_count = None
            try:
                max_count = int(self.txt_max_count.Text)
            except:
                pass
            
            max_scan = None
            try:
                max_scan = int(self.txt_max_scan.Text)
                if max_scan <= 0:
                    max_scan = None
            except:
                max_scan = None
            
            # Capture filters from UI
            filters = {}
            try:
                # Get selected telescopes from CheckedListBox
                selected_telescopes = []
                for i in range(self.lst_filter_telescope.Items.Count):
                    if self.lst_filter_telescope.GetItemChecked(i):
                        selected_telescopes.append(str(self.lst_filter_telescope.Items[i]))
                
                if selected_telescopes:
                    filters['telescopes'] = selected_telescopes
                    self.LogMessage("Filter: Telescopes - {0}".format(", ".join(selected_telescopes)))
                
                object_filter = self.txt_filter_object.Text.strip()
                if object_filter:
                    filters['object'] = object_filter
                    self.LogMessage("Filter: Object contains '{0}'".format(object_filter))
                
                # Picture type filter - collect all checked types
                selected_picture_types = []
                for i in range(self.lst_picture_types.Items.Count):
                    if self.lst_picture_types.GetItemChecked(i):
                        selected_picture_types.append(str(self.lst_picture_types.Items[i]).lower())
                
                # Only add filter if not all types are selected (partial selection)
                if selected_picture_types and len(selected_picture_types) < self.lst_picture_types.Items.Count:
                    filters['picture_types'] = selected_picture_types
                    self.LogMessage("Filter: Picture types - {0}".format(", ".join(selected_picture_types).upper()))
                elif selected_picture_types:
                    self.LogMessage("Filter: All picture types (PNG, JPEG, FITS)")
                
                # Date range filters from DateTimePicker controls
                if self.chk_use_start_date.Checked:
                    start_date = self.dtp_start_date.Value
                    start_date_str = start_date.ToString("yyyy-MM-dd")
                    filters['start_date'] = start_date_str
                    self.LogMessage("Filter: Start date >= {0}".format(start_date_str))
                
                if self.chk_use_end_date.Checked:
                    end_date = self.dtp_end_date.Value
                    end_date_str = end_date.ToString("yyyy-MM-dd")
                    filters['end_date'] = end_date_str
                    self.LogMessage("Filter: End date <= {0}".format(end_date_str))
            except:
                filters = {}
            
            # Capture dry-run setting
            dry_run = False
            try:
                dry_run = self.chk_dry_run.Checked
                if dry_run:
                    self.LogMessage("DRY RUN MODE - Preview only, no downloads")
            except:
                dry_run = False
            
            # Capture force redownload setting
            force_redownload = False
            try:
                force_redownload = self.chk_force_redownload.Checked
                if force_redownload:
                    self.LogMessage("FORCE REDOWNLOAD - Will ignore tracker")
            except:
                force_redownload = False
            
            # Get start image number
            start_image = 1
            try:
                start_image = int(self.txt_start_image.Text)
                if start_image < 1:
                    start_image = 1
                if start_image > 1:
                    self.LogMessage("Starting from image #{0}".format(start_image))
            except:
                start_image = 1
            
            # Capture download directory on UI thread (cannot access from background thread)
            # First check if there's a value in the Configuration tab's textbox
            download_dir = None
            try:
                if self.txt_download_dir and self.txt_download_dir.Text:
                    download_dir = self.txt_download_dir.Text.strip()
            except:
                pass
            
            # If not, get from saved config
            if not download_dir:
                download_dir = self.config.get('folders.base_path', 'SloohImages')
            
            # Make absolute if relative
            if download_dir and not os.path.isabs(download_dir):
                download_dir = os.path.abspath(download_dir)
            
            self.LogMessage("Download directory: {0}".format(download_dir))
                
            # Start download in background
            self.is_downloading = True
            self.btn_start.Enabled = False
            self.btn_pause.Enabled = True
            self.btn_stop.Enabled = True
            self.progress_overall.Value = 0
            
            # Start download thread, passing download_dir captured from UI thread
            thread = Threading.Thread(Threading.ThreadStart(
                lambda: self.DownloadWorker(mission_id, max_count, max_scan, start_image, download_dir, filters, dry_run, force_redownload)
            ))
            thread.IsBackground = True
            thread.Start()
            
        except Exception as ex:
            MessageBox.Show(
                "Error starting download: {0}".format(str(ex)),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            self.is_downloading = False
            
    def OnPauseDownload(self, sender, e):
        """Handle pause button"""
        if self.is_paused:
            self.is_paused = False
            self.btn_pause.Text = "Pause"
            # Set flag directly on download manager if it exists
            if self.download_manager:
                self.download_manager.is_paused = False
            self.UpdateStatus("Resumed")
            self.LogMessage("Resumed")
        else:
            self.is_paused = True
            self.btn_pause.Text = "Resume"
            # Set flag directly on download manager if it exists
            if self.download_manager:
                self.download_manager.is_paused = True
            self.UpdateStatus("Paused - waiting for current download to complete...")
            self.LogMessage("Paused - waiting for current download to complete...")
            
    def OnStopDownload(self, sender, e):
        """Handle stop button"""
        self.is_downloading = False
        self.is_paused = False
        
        # Set cancellation flags DIRECTLY on managers immediately
        if self.download_manager:
            self.download_manager.is_cancelled = True
            self.download_manager.is_paused = False
        if self.batch_manager:
            self.batch_manager.is_cancelled = True
        
        self.UpdateStatus("Stopping download - please wait...")
        self.LogMessage("Stopping download - waiting for active tasks to complete...")
        # Note: Buttons will be re-enabled in DownloadComplete() which is called
        # when the download thread finishes
        
    def OnRefreshMissions(self, sender, e):
        """Handle refresh missions"""
        if self.client is None:
            MessageBox.Show(
                "Please login first",
                "Not Logged In",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return
            
        self.LogMessage("Refreshing missions...")
        
    def OnSaveConfig(self, sender, e):
        """Handle save configuration"""
        try:
            self.config.set('folders.base_path', self.txt_download_dir.Text)
            self.config.set('download.threads', int(self.txt_max_concurrent.Text))
            self.config.set('download.rate_limit', int(self.txt_rate_limit.Text))
            self.config.set('download.max_retries', int(self.txt_max_retries.Text))
            self.config.set('folders.template', self.txt_template.Text)
            self.config.save()
            
            MessageBox.Show(
                "Configuration saved successfully",
                "Configuration",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
            self.LogMessage("Configuration saved")
        except Exception as ex:
            MessageBox.Show(
                "Error saving configuration: {0}".format(str(ex)),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            
    def OnBrowseFolder(self, sender, e):
        """Handle browse folder button"""
        try:
            dialog = FolderBrowserDialog()
            dialog.Description = "Select download directory"
            dialog.ShowNewFolderButton = True
            
            # Set initial directory if one exists
            if self.txt_download_dir.Text and os.path.exists(self.txt_download_dir.Text):
                dialog.SelectedPath = self.txt_download_dir.Text
            
            result = dialog.ShowDialog()
            if result == System.Windows.Forms.DialogResult.OK:
                self.txt_download_dir.Text = dialog.SelectedPath
                self.LogMessage("Download directory set to: {0}".format(dialog.SelectedPath))
        except Exception as ex:
            MessageBox.Show(
                "Error selecting folder: {0}".format(str(ex)),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            
    def OnAbout(self, sender, e):
        """Show about dialog"""
        MessageBox.Show(
            "Slooh Image Downloader\n\n" +
            "Version 2.0 (Stage 5 - Advanced Features)\n" +
            "IronPython Windows Forms Application\n\n" +
            "Download and organize your Slooh telescope images",
            "About",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        )
    
    def AutoLogin(self):
        """Auto-login with saved credentials"""
        try:
            username = self.txt_username.Text
            password = self.txt_password.Text
            
            if not username or not password:
                return
                
            # Create client and login
            base_url = self.config.get('slooh.base_url', 'https://app.slooh.com')
            self.client = SloohClient(base_url, self.logger)
            self.client.get_session_token()
            
            user_data = self.client.login(username, password)
            if user_data:
                display_name = user_data.get('displayName', username)
                
                # Update UI on UI thread
                def update_ui():
                    self.lbl_status.Text = "Logged in as {0}".format(display_name)
                    self.btn_start.Enabled = True
                    self.LogMessage("Auto-login successful: {0}".format(display_name))
                
                self.Invoke(Action(update_ui))
        except Exception as ex:
            # Log error but don't show message box (might be startup)
            def log_error():
                self.LogMessage("Auto-login failed: {0}".format(str(ex)))
            self.Invoke(Action(log_error))
    
    def OnDebugLevelChanged(self, sender, e):
        """Handle debug logging checkbox change"""
        try:
            if self.chk_debug_logging.Checked:
                # Set to DEBUG level
                self.config.set('logging.log_level', 'DEBUG')
                self.LogMessage("Debug logging ENABLED")
            else:
                # Set to INFO level
                self.config.set('logging.log_level', 'INFO')
                self.LogMessage("Debug logging disabled")
            
            self.config.save()
            
            MessageBox.Show(
                "Log level changed. Please restart the application for changes to take effect.",
                "Log Level Changed",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
        except Exception as ex:
            self.LogMessage("Error changing log level: {0}".format(str(ex)))
    
    def OnStartImageChanged(self, sender, e):
        """Handle start image number change - preview the date of that image"""
        try:
            start_num = int(self.txt_start_image.Text)
            
            # Only fetch date if not default value (1) and logged in
            if start_num != 1 and self.client and self.client.is_authenticated:
                # Fetch in background thread to avoid blocking UI
                def fetch_date():
                    try:
                        self.UpdateStatus("Fetching image #{0} date...".format(start_num))
                        
                        # Get single image at that position
                        response = self.client.get_pictures(first=start_num, max_count=1, mission_id=0, view_type='photoRoll')
                        images = response.get('imageList', [])
                        total_count = response.get('totalCount', 0)
                        
                        # Convert totalCount to int if it's a string
                        if isinstance(total_count, str):
                            total_count = int(total_count) if total_count else 0
                        
                        if images:
                            picture = images[0]
                            # Extract date from displayDate
                            display_date = picture.get('displayDate', '')
                            
                            if display_date:
                                # Update hint label and status with date and total count
                                date_text = "(Date: {0}) - Total: {1:,} images".format(display_date, total_count)
                                self.UpdateStartImageHint(date_text)
                                self.UpdateStatus("Image #{0} is from {1} (Total: {2:,} images)".format(start_num, display_date, total_count))
                                self.LogMessage("Start image #{0} is from {1} (Total: {2:,} images)".format(start_num, display_date, total_count))
                            else:
                                hint_text = "(Date unavailable) - Total: {0:,} images".format(total_count)
                                self.UpdateStartImageHint(hint_text)
                                self.UpdateStatus("Image #{0} found but date unavailable (Total: {1:,} images)".format(start_num, total_count))
                        else:
                            self.UpdateStartImageHint("(Image not found)")
                            self.UpdateStatus("Image #{0} not found".format(start_num))
                            
                    except Exception as ex:
                        self.UpdateStartImageHint("(Error fetching date)")
                        self.UpdateStatus("Error fetching image date: {0}".format(str(ex)))
                
                # Run in background thread
                thread = Threading.Thread(Threading.ThreadStart(fetch_date))
                thread.IsBackground = True
                thread.Start()
            else:
                # Reset to default hint
                self.UpdateStartImageHint("(1 = most recent)")
                
        except ValueError:
            # Invalid number - reset hint
            self.UpdateStartImageHint("(1 = most recent)")
        
    def OnExit(self, sender, e):
        """Handle exit"""
        self.Close()
        
    def DownloadWorker(self, mission_id, max_count, max_scan, start_image, download_dir, filters=None, dry_run=False, force_redownload=False):
        """Background download worker"""
        try:
            # Update config with download directory FIRST
            if download_dir:
                self.config.set('folders.base_path', download_dir)
                self.UpdateStatus("Using directory: {0}".format(download_dir))
            
            # Pass the ConfigurationManager itself (not config_dict)
            # because FileOrganizer expects dot-notation config.get()
            self.download_manager = DownloadManager(self.config.config, self.logger)
            file_organizer = FileOrganizer(self.config, self.logger)
            
            # DownloadTracker only needs the tracker file path
            tracker_file = self.config.get('tracking.tracker_file', 'data/download_tracker.json')
            download_tracker = DownloadTracker(tracker_file)
            download_tracker.load()
            
            self.batch_manager = BatchManager(
                self.config.config,
                self.client,
                self.download_manager,
                file_organizer,
                download_tracker,
                self.logger
            )
            
            # Setup progress callback and link control flags
            def on_progress(progress):
                # Sync pause state to download manager
                self.download_manager.is_paused = self.is_paused
                # Sync cancel state to download manager
                self.download_manager.is_cancelled = not self.is_downloading
                
                if self.is_paused:
                    return
                    
                self.UpdateProgress(progress)
                
            self.download_manager.on_progress = on_progress
            
            # Reset control flags for new session
            self.batch_manager.is_cancelled = False
            self.download_manager.reset_control_flags()
            
            # Download with filters and dry_run
            if mission_id is not None and mission_id > 0:
                self.UpdateStatus("Downloading mission {0}...".format(mission_id))
                self.LogMessage("Requesting pictures for mission: {0}".format(mission_id))
                stats = self.batch_manager.download_all_pictures(
                    mission_id=mission_id, 
                    max_total=max_count,
                    max_scan=max_scan,
                    start_image=start_image,
                    filters=filters,
                    dry_run=dry_run,
                    force_redownload=force_redownload
                )
            else:
                self.UpdateStatus("Downloading all missions...")
                self.LogMessage("Requesting all pictures (no mission filter)")
                stats = self.batch_manager.download_all_pictures(
                    mission_id=0, 
                    max_total=max_count,
                    max_scan=max_scan,
                    start_image=start_image,
                    filters=filters,
                    dry_run=dry_run,
                    force_redownload=force_redownload
                )
                
            # Update statistics
            self.UpdateStats(stats)
            
            if dry_run:
                queued_count = stats.get('queued', 0)
                self.UpdateStatus("Dry run complete - Found {0} images (preview only)".format(queued_count))
                self.LogMessage("DRY RUN: {0} images would be downloaded".format(queued_count))
            else:
                self.UpdateStatus("Download complete")
            
        except Exception as ex:
            self.UpdateStatus("Error: {0}".format(str(ex)))
        finally:
            self.DownloadComplete()
    
    def UpdateStartImageHint(self, hint_text):
        """Update start image hint label (thread-safe)"""
        if self.InvokeRequired:
            self.Invoke(Action[str](self.UpdateStartImageHint), hint_text)
            return
        self.lbl_start_image_hint.Text = hint_text
            
    def UpdateProgress(self, progress):
        """Update progress display (thread-safe)"""
        if self.InvokeRequired:
            self.Invoke(Action[object](self.UpdateProgress), progress)
            return
            
        try:
            percent = progress.get('percent', 0)
            self.progress_overall.Value = min(100, max(0, int(percent)))
            
            current = progress.get('current', 0)
            total = progress.get('total', 0)
            
            # Include batch information if available
            if 'batch_number' in progress:
                batch_num = progress['batch_number']
                batch_size = progress.get('batch_size', 0)
                self.lbl_current_file.Text = "Batch #{0}: Downloading {1} of {2}".format(batch_num, current, batch_size)
            else:
                self.lbl_current_file.Text = "Downloading {0} of {1}".format(current, total)
                
        except Exception as ex:
            self.LogMessage("Error updating progress: {0}".format(str(ex)))
            
    def UpdateStatus(self, message):
        """Update status label (thread-safe)"""
        if self.InvokeRequired:
            self.Invoke(Action[str](self.UpdateStatus), message)
            return
            
        self.lbl_status.Text = message
        self.LogMessage(message)
    
    def UpdateStartImageHint(self, hint_text):
        """Update start image hint label (thread-safe)"""
        if self.InvokeRequired:
            self.Invoke(Action[str](self.UpdateStartImageHint), hint_text)
            return
        self.lbl_start_image_hint.Text = hint_text
        
    def UpdateStats(self, stats):
        """Update statistics display (thread-safe)"""
        if self.InvokeRequired:
            self.Invoke(Action[object](self.UpdateStats), stats)
            return
            
        try:
            # Handle both formats: 'total'/'completed' and 'queued'/'downloaded'
            total = stats.get('total', stats.get('queued', 0))
            completed = stats.get('completed', stats.get('downloaded', 0))
            failed = stats.get('failed', 0)
            
            self.lbl_total_downloads.Text = str(total)
            self.lbl_successful.Text = str(completed)
            self.lbl_failed.Text = str(failed)
            
            total_bytes = stats.get('total_bytes', 0)
            mb = total_bytes / (1024.0 * 1024.0)
            self.lbl_total_size.Text = "{0:.2f} MB".format(mb)
            
        except Exception as ex:
            self.LogMessage("Error updating stats: {0}".format(str(ex)))
            
    def DownloadComplete(self):
        """Reset UI after download completes (thread-safe)"""
        if self.InvokeRequired:
            self.Invoke(Action(self.DownloadComplete))
            return
            
        self.is_downloading = False
        self.is_paused = False
        self.btn_start.Enabled = True
        self.btn_pause.Enabled = False
        self.btn_stop.Enabled = False
        self.btn_pause.Text = "Pause"
        
        # Clear manager references (they'll be recreated on next download)
        self.download_manager = None
        self.batch_manager = None
        
        # Load updated history and statistics after download completes
        self.LoadHistory()
        self.LoadStatistics()
        
    def LoadHistory(self):
        """Load download history into grid (thread-safe)"""
        if self.InvokeRequired:
            self.Invoke(Action(self.LoadHistory))
            return
            
        try:
            # Load tracker
            tracker_file = self.config.get('tracking.tracker_file', 'data/download_tracker.json')
            tracker = DownloadTracker(tracker_file)
            tracker.load()
            
            # Clear existing rows
            self.grid_history.Rows.Clear()
            
            # Get all downloaded images
            images = tracker.data.get('images', {})
            
            # Add rows (most recent first)
            items = sorted(images.items(), key=lambda x: x[1].get('download_date', ''), reverse=True)
            
            for image_key, image_data in items[:100]:  # Limit to 100 most recent
                # Get title - use object_name or filename if object_name is empty
                title = image_data.get('object_name', '')
                if not title or title == 'Unknown':
                    # Fallback to filename without extension
                    filename = image_data.get('filename', 'Unknown')
                    title = filename.rsplit('.', 1)[0] if filename else 'Unknown'
                
                telescope = image_data.get('telescope_name', 'Unknown')
                download_date = image_data.get('download_date', '')
                file_path = image_data.get('file_path', '')
                
                # Format date for display
                if download_date:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(download_date.replace('Z', '+00:00').split('+')[0])
                        download_date = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                
                self.grid_history.Rows.Add(
                    image_key,
                    title,
                    download_date,
                    telescope,
                    "Downloaded",
                    file_path
                )
            
            self.LogMessage("Loaded {0} history items".format(len(items)))
            
        except Exception as ex:
            self.LogMessage("Error loading history: {0}".format(str(ex)))
            
    def LoadStatistics(self):
        """Load statistics from tracker (thread-safe)"""
        if self.InvokeRequired:
            self.Invoke(Action(self.LoadStatistics))
            return
            
        try:
            # Load tracker
            tracker_file = self.config.get('tracking.tracker_file', 'data/download_tracker.json')
            tracker = DownloadTracker(tracker_file)
            tracker.load()
            
            # Get statistics
            stats = tracker.get_statistics()
            if not stats:
                return
            
            # Update labels with correct field names
            total_images = stats.get('total_images', 0)
            self.lbl_total_downloads.Text = str(total_images)
            self.lbl_successful.Text = str(total_images)
            self.lbl_failed.Text = "0"  # Tracker doesn't store failures
            
            total_mb = stats.get('total_bytes', 0) / (1024.0 * 1024.0)
            self.lbl_total_size.Text = "{0:.2f} MB".format(total_mb)
            
            # Calculate average speed (not available from tracker, show N/A)
            self.lbl_avg_speed.Text = "N/A"
            
            # Session stats (last session)
            sessions = tracker.data.get('sessions', [])
            if sessions:
                last_session = sessions[-1]
                self.lbl_session_downloads.Text = str(last_session.get('images_downloaded', 0))
            else:
                self.lbl_session_downloads.Text = "0"
            
            self.LogMessage("Statistics updated - {0} images, {1:.2f} MB".format(total_images, total_mb))
            
        except Exception as ex:
            self.LogMessage("Error loading statistics: {0}".format(str(ex)))
    
    # Stage 5: Advanced Features Event Handlers
    
    def OnExportCSV(self, sender, e):
        """Export download history to CSV"""
        try:
            from System.Windows.Forms import SaveFileDialog, DialogResult
            
            dlg = SaveFileDialog()
            dlg.Filter = "CSV Files (*.csv)|*.csv|All Files (*.*)|*.*"
            dlg.DefaultExt = "csv"
            dlg.FileName = "slooh_downloads.csv"
            
            if dlg.ShowDialog() == DialogResult.OK:
                tracker_file = self.config.get('tracking.tracker_file', 'data/download_tracker.json')
                tracker = DownloadTracker(tracker_file)
                tracker.load()
                
                from report_generator import ReportGenerator
                generator = ReportGenerator(tracker, self.logger)
                
                if generator.export_csv(dlg.FileName):
                    MessageBox.Show(
                        "CSV report exported successfully",
                        "Export Complete",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Information
                    )
                    self.LogMessage("Exported CSV: {0}".format(dlg.FileName))
                else:
                    MessageBox.Show(
                        "Failed to export CSV report",
                        "Export Error",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    )
        except Exception as ex:
            MessageBox.Show(
                "Export error: {0}".format(str(ex)),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            
    def OnExportHTML(self, sender, e):
        """Export download history to HTML"""
        try:
            from System.Windows.Forms import SaveFileDialog, DialogResult
            
            dlg = SaveFileDialog()
            dlg.Filter = "HTML Files (*.html)|*.html|All Files (*.*)|*.*"
            dlg.DefaultExt = "html"
            dlg.FileName = "slooh_downloads.html"
            
            if dlg.ShowDialog() == DialogResult.OK:
                tracker_file = self.config.get('tracking.tracker_file', 'data/download_tracker.json')
                tracker = DownloadTracker(tracker_file)
                tracker.load()
                
                from report_generator import ReportGenerator
                generator = ReportGenerator(tracker, self.logger)
                
                if generator.export_html(dlg.FileName):
                    MessageBox.Show(
                        "HTML report exported successfully",
                        "Export Complete",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Information
                    )
                    self.LogMessage("Exported HTML: {0}".format(dlg.FileName))
                else:
                    MessageBox.Show(
                        "Failed to export HTML report",
                        "Export Error",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    )
        except Exception as ex:
            MessageBox.Show(
                "Export error: {0}".format(str(ex)),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            
    def OnExportStatistics(self, sender, e):
        """Export statistics report"""
        try:
            from System.Windows.Forms import SaveFileDialog, DialogResult
            
            dlg = SaveFileDialog()
            dlg.Filter = "HTML Files (*.html)|*.html|Text Files (*.txt)|*.txt|All Files (*.*)|*.*"
            dlg.DefaultExt = "html"
            dlg.FileName = "slooh_statistics.html"
            
            if dlg.ShowDialog() == DialogResult.OK:
                tracker_file = self.config.get('tracking.tracker_file', 'data/download_tracker.json')
                tracker = DownloadTracker(tracker_file)
                tracker.load()
                
                from report_generator import ReportGenerator
                generator = ReportGenerator(tracker, self.logger)
                
                # Determine format based on extension
                format = 'html' if dlg.FileName.lower().endswith('.html') else 'txt'
                
                if generator.export_statistics_report(dlg.FileName, format=format):
                    MessageBox.Show(
                        "Statistics report exported successfully",
                        "Export Complete",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Information
                    )
                    self.LogMessage("Exported statistics: {0}".format(dlg.FileName))
                else:
                    MessageBox.Show(
                        "Failed to export statistics report",
                        "Export Error",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    )
        except Exception as ex:
            MessageBox.Show(
                "Export error: {0}".format(str(ex)),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            
    def OnVerifyDownloads(self, sender, e):
        """Verify all tracked downloads still exist"""
        try:
            tracker_file = self.config.get('tracking.tracker_file', 'data/download_tracker.json')
            tracker = DownloadTracker(tracker_file)
            tracker.load()
            
            self.LogMessage("Verifying downloads...")
            results = tracker.verify_downloads()
            
            message = "Verification Results:\n\n"
            message += "Total tracked: {0}\n".format(results['total'])
            message += "Valid: {0}\n".format(results['valid'])
            message += "Missing: {0}\n".format(results['missing'])
            message += "Errors: {0}".format(results['errors'])
            
            if results['missing'] > 0:
                message += "\n\nMissing files:\n"
                for mf in results['missing_files'][:10]:  # Show first 10
                    message += "- {0}\n".format(mf.get('filename', 'Unknown'))
                if results['missing'] > 10:
                    message += "... and {0} more".format(results['missing'] - 10)
            
            MessageBox.Show(
                message,
                "Verification Complete",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
            self.LogMessage("Verification complete: {0} valid, {1} missing".format(
                results['valid'], results['missing']))
                
        except Exception as ex:
            MessageBox.Show(
                "Verification error: {0}".format(str(ex)),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            
    def OnFindOrphaned(self, sender, e):
        """Find orphaned files not in tracker"""
        try:
            tracker_file = self.config.get('tracking.tracker_file', 'data/download_tracker.json')
            tracker = DownloadTracker(tracker_file)
            tracker.load()
            
            base_path = self.config.get('folders.base_path', 'SloohImages')
            if not os.path.isabs(base_path):
                base_path = os.path.abspath(base_path)
            
            self.LogMessage("Scanning for orphaned files in: {0}".format(base_path))
            orphaned = tracker.find_orphaned_files(base_path)
            
            message = "Found {0} orphaned file(s)\n\n".format(len(orphaned))
            
            if orphaned:
                message += "Orphaned files:\n"
                for f in orphaned[:20]:  # Show first 20
                    message += "- {0}\n".format(os.path.basename(f))
                if len(orphaned) > 20:
                    message += "... and {0} more".format(len(orphaned) - 20)
            else:
                message = "No orphaned files found. All files are tracked."
            
            MessageBox.Show(
                message,
                "Orphaned Files",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
            self.LogMessage("Found {0} orphaned files".format(len(orphaned)))
                
        except Exception as ex:
            MessageBox.Show(
                "Error finding orphaned files: {0}".format(str(ex)),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            
    def OnCleanMissing(self, sender, e):
        """Remove missing files from tracker"""
        try:
            result = MessageBox.Show(
                "This will remove entries for files that no longer exist on disk.\n\nContinue?",
                "Confirm Cleanup",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Question
            )
            
            if result == DialogResult.Yes:
                tracker_file = self.config.get('tracking.tracker_file', 'data/download_tracker.json')
                tracker = DownloadTracker(tracker_file)
                tracker.load()
                
                removed = tracker.remove_missing_from_tracker()
                
                MessageBox.Show(
                    "Removed {0} missing entries from tracker".format(removed),
                    "Cleanup Complete",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                )
                self.LogMessage("Cleaned {0} missing entries".format(removed))
                
                # Reload history
                self.LoadHistory()
                self.LoadStatistics()
                
        except Exception as ex:
            MessageBox.Show(
                "Cleanup error: {0}".format(str(ex)),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            
    def OnCleanSessions(self, sender, e):
        """Clean old session data"""
        try:
            tracker_file = self.config.get('tracking.tracker_file', 'data/download_tracker.json')
            tracker = DownloadTracker(tracker_file)
            tracker.load()
            
            tracker.clear_session_data(keep_last_n=10)
            
            MessageBox.Show(
                "Old session data cleaned. Kept last 10 sessions.",
                "Cleanup Complete",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
            self.LogMessage("Cleaned old session data")
            self.LoadStatistics()
                
        except Exception as ex:
            MessageBox.Show(
                "Cleanup error: {0}".format(str(ex)),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            
    def OnBackupTracker(self, sender, e):
        """Backup tracker file"""
        try:
            tracker_file = self.config.get('tracking.tracker_file', 'data/download_tracker.json')
            tracker = DownloadTracker(tracker_file)
            tracker.load()
            
            if tracker.backup():
                MessageBox.Show(
                    "Tracker backed up successfully",
                    "Backup Complete",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                )
                self.LogMessage("Tracker backed up")
            else:
                MessageBox.Show(
                    "Failed to backup tracker",
                    "Backup Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                )
        except Exception as ex:
            MessageBox.Show(
                "Backup error: {0}".format(str(ex)),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
        
    def LogMessage(self, message):
        """Add message to log (thread-safe)"""
        if self.InvokeRequired:
            self.Invoke(Action[str](self.LogMessage), message)
            return
            
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.txt_log.AppendText("[{0}] {1}\r\n".format(timestamp, message))
        except:
            pass


def main():
    """Main entry point"""
    try:
        Application.EnableVisualStyles()
        Application.SetCompatibleTextRenderingDefault(False)
        
        form = SloohDownloaderForm()
        Application.Run(form)
        
    except Exception as e:
        MessageBox.Show(
            "Fatal error: {0}".format(str(e)),
            "Error",
            MessageBoxButtons.OK,
            MessageBoxIcon.Error
        )
        import traceback
        traceback.print_exc()
        

if __name__ == '__main__':
    main()
