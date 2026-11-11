using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Markup;
using System.Windows.Media;
using System.Windows.Shapes;

namespace DmCTrainerApp
{
    internal static class Theme
    {
        public static readonly SolidColorBrush BgRoot = Brush("#0A0C10");
        public static readonly SolidColorBrush BgPanel = Brush("#11151E");
        public static readonly SolidColorBrush BgCard = Brush("#161A24");
        public static readonly SolidColorBrush BgCardHdr = Brush("#1B202C");
        public static readonly SolidColorBrush BgRowHover = Brush("#1E2433");
        public static readonly SolidColorBrush BgRowActive = Brush("#22121A");
        public static readonly SolidColorBrush BgInput = Brush("#0C0F16");
        public static readonly SolidColorBrush BgSwitchOff = Brush("#242A38");
        public static readonly SolidColorBrush BorderSubtle = Brush("#222838");
        public static readonly SolidColorBrush BorderStrong = Brush("#333D54");
        public static readonly SolidColorBrush Crimson = Brush("#E11D48");
        public static readonly SolidColorBrush CrimsonSoft = Brush("#361522");
        public static readonly SolidColorBrush CrimsonText = Brush("#FDA4AF");
        public static readonly SolidColorBrush Cyan = Brush("#38BDF8");
        public static readonly SolidColorBrush CyanSoft = Brush("#142C3D");
        public static readonly SolidColorBrush CyanText = Brush("#BAE6FD");
        public static readonly SolidColorBrush Amber = Brush("#F59E0B");
        public static readonly SolidColorBrush AmberSoft = Brush("#2F2312");
        public static readonly SolidColorBrush AmberText = Brush("#FDE68A");
        public static readonly SolidColorBrush Green = Brush("#10B981");
        public static readonly SolidColorBrush TextMain = Brush("#EDF2F7");
        public static readonly SolidColorBrush TextMuted = Brush("#8B95A8");
        public static readonly SolidColorBrush TextDim = Brush("#5D677A");
        public static readonly SolidColorBrush White = Brush("#FFFFFF");

        public static SolidColorBrush Brush(string hex)
        {
            var b = (SolidColorBrush)new BrushConverter().ConvertFromString(hex);
            b.Freeze();
            return b;
        }
    }

    internal sealed class SegSwitchControl : Border
    {
        private readonly Border offPill, onPill;
        private readonly TextBlock offLbl, onLbl;
        public bool IsOn { get; private set; }
        public event Action<bool> Toggled;

        public SegSwitchControl()
        {
            CornerRadius = new CornerRadius(13);
            Background = Theme.BgInput;
            BorderBrush = Theme.BorderSubtle;
            BorderThickness = new Thickness(1);
            Padding = new Thickness(2);
            Cursor = Cursors.Hand;
            VerticalAlignment = VerticalAlignment.Center;

            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            offPill = new Border { CornerRadius = new CornerRadius(11), Padding = new Thickness(11, 3, 11, 3) };
            offLbl = new TextBlock { Text = "Off", FontSize = 11.5, FontWeight = FontWeights.SemiBold };
            offPill.Child = offLbl;
            Grid.SetColumn(offPill, 0);

            onPill = new Border { CornerRadius = new CornerRadius(11), Padding = new Thickness(11, 3, 11, 3) };
            onLbl = new TextBlock { Text = "On", FontSize = 11.5, FontWeight = FontWeights.SemiBold };
            onPill.Child = onLbl;
            Grid.SetColumn(onPill, 1);

            grid.Children.Add(offPill);
            grid.Children.Add(onPill);
            Child = grid;

            MouseLeftButtonUp += delegate
            {
                bool next = !IsOn;
                SetVisualState(next);
                if (Toggled != null) Toggled(next);
            };
            SetVisualState(false);
        }

        public void SetVisualState(bool on)
        {
            IsOn = on;
            offPill.Background = on ? Brushes.Transparent : Theme.BgSwitchOff;
            offLbl.Foreground = on ? Theme.TextDim : Theme.TextMain;
            onPill.Background = on ? Theme.Crimson : Brushes.Transparent;
            onLbl.Foreground = on ? Theme.White : Theme.TextDim;
        }
    }

    internal sealed class ModRowRefs
    {
        public ModSpec Spec;
        public Border RowBorder, BoltBox;
        public TextBlock BoltIcon, RangeLabel;
        public SegSwitchControl Switch;
        public Button HotkeyBtn;
        public Slider RangeSlider;
        public TextBox NumInput;
        public bool IsSliderDragging;
    }

    internal sealed class CatSectionRefs
    {
        public CategorySpec Spec;
        public Border Card, BodyWrapper, BadgePill;
        public TextBlock BadgeText, Chevron;
        public bool Collapsed;
    }

    internal sealed class TrainerWindow : Window
    {
        [DllImport("dwmapi.dll")]
        private static extern int DwmSetWindowAttribute(IntPtr hwnd, int attr, ref int attrValue, int attrSize);

        private readonly IpcClient ipc;
        private readonly Process backendProc;
        private readonly List<CategorySpec> categories;
        private readonly Dictionary<string, ModRowRefs> rowMap = new Dictionary<string, ModRowRefs>();
        private readonly Dictionary<string, CatSectionRefs> catMap = new Dictionary<string, CatSectionRefs>();
        private readonly Dictionary<string, Button> hkActionBtns = new Dictionary<string, Button>();
        private readonly Dictionary<string, Button> tabButtons = new Dictionary<string, Button>();
        private readonly TextBlock[] tpSlotCoords = new TextBlock[3];

        private readonly Dictionary<string, bool> localToggles = new Dictionary<string, bool>();
        private readonly Dictionary<string, double> localValues = new Dictionary<string, double>();
        private readonly Dictionary<string, string> localHotkeys = new Dictionary<string, string>();
        private bool localSound = true;
        private string activeCat = "all";
        private string searchQuery = "";
        private string bindingAction;
        private volatile bool isClosing;

        private Ellipse connDot;
        private Border charPill, hookPill;
        private TextBlock connText, charText, hookText, lastEventText, coordsText, activeCountText;
        private TextBlock tStyleRank, tStylePts, tHp, tDt, tOd, tRedOrbs, tGoldUp, tKeys, tStars, tFrags, tTimerEnemies;
        private Button soundBtn;
        private StackPanel categoriesHost;
        private Grid hotkeyModalOverlay;
        private TextBlock hotkeyTargetLabel;

        private readonly Style darkSliderStyle;

        public TrainerWindow(IpcClient client, Process proc)
        {
            ipc = client;
            backendProc = proc;
            categories = TrainerCatalog.BuildCategories();

            Title = "DmC: Devil May Cry - Ultimate Trainer";
            Width = 1220;
            Height = 860;
            MinWidth = 960;
            MinHeight = 660;
            WindowStartupLocation = WindowStartupLocation.CenterScreen;
            Background = Theme.BgRoot;
            Foreground = Theme.TextMain;
            FontFamily = new FontFamily("Segoe UI");

            darkSliderStyle = (Style)XamlReader.Parse(
                "<Style xmlns='http://schemas.microsoft.com/winfx/2006/xaml/presentation' " +
                "xmlns:x='http://schemas.microsoft.com/winfx/2006/xaml' TargetType='Slider'>" +
                "<Setter Property='Height' Value='22'/><Setter Property='VerticalAlignment' Value='Center'/>" +
                "<Setter Property='Template'><Setter.Value><ControlTemplate TargetType='Slider'>" +
                "<Grid VerticalAlignment='Center'>" +
                "<Border Height='5' CornerRadius='2.5' Background='#252C3D' VerticalAlignment='Center'/>" +
                "<Track x:Name='PART_Track'>" +
                "<Track.DecreaseRepeatButton><RepeatButton Command='Slider.DecreaseLarge' IsTabStop='False'><RepeatButton.Template><ControlTemplate TargetType='RepeatButton'><Border Height='5' CornerRadius='2.5' Background='#E11D48' VerticalAlignment='Center'/></ControlTemplate></RepeatButton.Template></RepeatButton></Track.DecreaseRepeatButton>" +
                "<Track.IncreaseRepeatButton><RepeatButton Command='Slider.IncreaseLarge' IsTabStop='False'><RepeatButton.Template><ControlTemplate TargetType='RepeatButton'><Border Height='5' Background='Transparent'/></ControlTemplate></RepeatButton.Template></RepeatButton></Track.IncreaseRepeatButton>" +
                "<Track.Thumb><Thumb><Thumb.Template><ControlTemplate TargetType='Thumb'><Ellipse Width='14' Height='14' Fill='#F8FAFC' Stroke='#E11D48' StrokeThickness='2.5' Cursor='Hand'/></ControlTemplate></Thumb.Template></Thumb></Track.Thumb>" +
                "</Track></Grid></ControlTemplate></Setter.Value></Setter></Style>");

            var darkScrollBarStyle = (Style)XamlReader.Parse(
                "<Style xmlns='http://schemas.microsoft.com/winfx/2006/xaml/presentation' " +
                "xmlns:x='http://schemas.microsoft.com/winfx/2006/xaml' TargetType='ScrollBar'>" +
                "<Setter Property='Width' Value='10'/><Setter Property='Background' Value='#0A0C10'/>" +
                "<Setter Property='Template'><Setter.Value><ControlTemplate TargetType='ScrollBar'>" +
                "<Grid Background='{TemplateBinding Background}'><Track x:Name='PART_Track' IsDirectionReversed='True'>" +
                "<Track.Thumb><Thumb><Thumb.Template><ControlTemplate TargetType='Thumb'><Border CornerRadius='4' Background='#2B3447' Margin='2'/></ControlTemplate></Thumb.Template></Thumb></Track.Thumb>" +
                "</Track></Grid></ControlTemplate></Setter.Value></Setter></Style>");

            Resources.Add(typeof(ScrollBar), darkScrollBarStyle);

            BuildVisualTree();

            SourceInitialized += OnSourceInitializedDarkTitleBar;
            PreviewKeyDown += OnWindowPreviewKeyDown;
            Closing += OnWindowClosing;

            if (backendProc != null)
            {
                backendProc.OutputDataReceived += OnBackendOutput;
                backendProc.EnableRaisingEvents = true;
                backendProc.Exited += delegate
                {
                    if (!isClosing)
                    {
                        Dispatcher.BeginInvoke(new Action(delegate
                        {
                            connDot.Fill = Theme.Crimson;
                            connText.Text = "Backend exited unexpectedly.";
                        }));
                    }
                };
                backendProc.BeginOutputReadLine();
            }
        }

        private void OnBackendOutput(object sender, DataReceivedEventArgs e)
        {
            if (isClosing || string.IsNullOrEmpty(e.Data)) return;
            try
            {
                var state = ipc.DeserializeLine(e.Data);
                if (state != null)
                {
                    Dispatcher.BeginInvoke(new Action(delegate { ApplyServerState(state); }));
                }
            }
            catch { }
        }

        private void OnSourceInitializedDarkTitleBar(object sender, EventArgs e)
        {
            try
            {
                IntPtr hwnd = new WindowInteropHelper(this).Handle;
                int dark = 1;
                if (DwmSetWindowAttribute(hwnd, 20, ref dark, 4) != 0)
                    DwmSetWindowAttribute(hwnd, 19, ref dark, 4);
            }
            catch { }
        }

        private void OnWindowClosing(object sender, System.ComponentModel.CancelEventArgs e)
        {
            isClosing = true;
            ipc.Send(Dict("cmd", "quit"));
            try { backendProc.StandardInput.Close(); } catch { }
            ThreadPool.QueueUserWorkItem(delegate
            {
                try
                {
                    if (backendProc != null && !backendProc.HasExited && !backendProc.WaitForExit(1000))
                        backendProc.Kill();
                }
                catch { }
            });
        }

        private void BuildVisualTree()
        {
            var rootGrid = new Grid { Background = Theme.BgRoot };
            var dock = new DockPanel { LastChildFill = true };

            var hdr = BuildHeader(); DockPanel.SetDock(hdr, Dock.Top); dock.Children.Add(hdr);
            var tele = BuildTelemetryBar(); DockPanel.SetDock(tele, Dock.Top); dock.Children.Add(tele);
            var bar = BuildToolbar(); DockPanel.SetDock(bar, Dock.Top); dock.Children.Add(bar);
            var ftr = BuildFooter(); DockPanel.SetDock(ftr, Dock.Bottom); dock.Children.Add(ftr);

            var scroll = new ScrollViewer
            {
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled,
                Background = Theme.BgRoot
            };
            categoriesHost = new StackPanel { Margin = new Thickness(20, 14, 20, 24) };
            BuildCategoryCards();
            scroll.Content = categoriesHost;
            dock.Children.Add(scroll);

            rootGrid.Children.Add(dock);
            hotkeyModalOverlay = BuildHotkeyModal();
            rootGrid.Children.Add(hotkeyModalOverlay);
            Content = rootGrid;
        }

        private UIElement BuildHeader()
        {
            var grad = new LinearGradientBrush(
                (Color)ColorConverter.ConvertFromString("#18111B"),
                (Color)ColorConverter.ConvertFromString("#0D1520"),
                new Point(0, 0), new Point(1, 1));
            grad.Freeze();

            var badgeGrad = new LinearGradientBrush(
                (Color)ColorConverter.ConvertFromString("#BE123C"),
                (Color)ColorConverter.ConvertFromString("#1D4ED8"),
                new Point(0, 0), new Point(1, 1));
            badgeGrad.Freeze();

            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var left = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            left.Children.Add(new Border
            {
                Width = 44, Height = 44, CornerRadius = new CornerRadius(10),
                Background = badgeGrad, BorderBrush = Theme.Brush("#38FFFFFF"), BorderThickness = new Thickness(1),
                Margin = new Thickness(0, 0, 14, 0),
                Child = MakeText("DmC", 15, FontWeights.ExtraBold, Theme.White, HorizontalAlignment.Center)
            });

            var titleStack = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
            var titleRow = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            titleRow.Children.Add(MakeText("DmC: Devil May Cry", 18.5, FontWeights.Bold, Theme.TextMain));
            titleRow.Children.Add(MakePill("UE3 Reflection + AOB", Theme.CyanSoft, Theme.Brush("#4038BDF8"), Theme.Cyan, new Thickness(10, 0, 0, 0)));
            titleStack.Children.Add(titleRow);

            var statusRow = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(0, 4, 0, 0) };
            connDot = new Ellipse { Width = 8, Height = 8, Fill = Theme.Amber, Margin = new Thickness(0, 0, 7, 0), VerticalAlignment = VerticalAlignment.Center };
            connText = MakeText("Waiting for DMC-DevilMayCry.exe...", 12, FontWeights.Normal, Theme.TextMuted);
            charText = MakeText("", 11, FontWeights.SemiBold, Theme.CyanText);
            charPill = WrapPill(charText, Theme.CyanSoft, new Thickness(8, 0, 0, 0));
            hookText = MakeText("", 11, FontWeights.Normal, Theme.TextMuted);
            hookPill = WrapPill(hookText, Theme.Brush("#1C2230"), new Thickness(8, 0, 0, 0));

            statusRow.Children.Add(connDot);
            statusRow.Children.Add(connText);
            statusRow.Children.Add(charPill);
            statusRow.Children.Add(hookPill);
            titleStack.Children.Add(statusRow);
            left.Children.Add(titleStack);
            Grid.SetColumn(left, 0);
            grid.Children.Add(left);

            var right = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            soundBtn = MakeFlatButton("Sound On", Theme.CyanSoft, Theme.Brush("#6638BDF8"), Theme.TextMain);
            soundBtn.Margin = new Thickness(0, 0, 10, 0);
            soundBtn.Click += delegate
            {
                localSound = !localSound;
                UpdateSoundButtonVisual();
                ipc.Send(Dict("cmd", "sound", "enabled", localSound));
            };
            var disableBtn = MakeFlatButton("Disable All  [Home]", Theme.CrimsonSoft, Theme.Brush("#77E11D48"), Theme.CrimsonText);
            disableBtn.Click += delegate { ipc.Send(Dict("cmd", "action", "action", "disable_all")); };
            right.Children.Add(soundBtn);
            right.Children.Add(disableBtn);
            Grid.SetColumn(right, 1);
            grid.Children.Add(right);

            return new Border
            {
                Background = grad, BorderBrush = Theme.BorderSubtle, BorderThickness = new Thickness(0, 0, 0, 1),
                Padding = new Thickness(22, 14, 22, 14), Child = grid
            };
        }

        private UIElement BuildTelemetryBar()
        {
            var ugrid = new UniformGrid { Columns = 5, Rows = 2 };
            var styleHost = new StackPanel { Orientation = Orientation.Horizontal };
            tStyleRank = MakeText("-", 14, FontWeights.ExtraBold, Theme.TextDim);
            tStyleRank.Margin = new Thickness(0, 0, 8, 0);
            tStylePts = MakeText("0", 12, FontWeights.Normal, Theme.TextMuted);
            tStylePts.VerticalAlignment = VerticalAlignment.Bottom;
            styleHost.Children.Add(tStyleRank);
            styleHost.Children.Add(tStylePts);
            ugrid.Children.Add(MakeTeleCard("STYLE", styleHost));

            ugrid.Children.Add(MakeTeleCard("HEALTH", tHp = MakeTeleVal("0 / 0", Theme.TextMain)));
            ugrid.Children.Add(MakeTeleCard("DEVIL TRIGGER", tDt = MakeTeleVal("0 / 0", Theme.TextMain)));
            ugrid.Children.Add(MakeTeleCard("OVERDRIVE", tOd = MakeTeleVal("0 / 100", Theme.TextMain)));
            ugrid.Children.Add(MakeTeleCard("RED ORBS", tRedOrbs = MakeTeleVal("0", Theme.CrimsonText)));
            ugrid.Children.Add(MakeTeleCard("GOLD · UPGRADES", tGoldUp = MakeTeleVal("0 · 0 pt", Theme.TextMain)));
            ugrid.Children.Add(MakeTeleCard("KEYS (C / A / G / I)", tKeys = MakeTeleVal("0 / 0 / 0 / 0", Theme.TextMain)));
            ugrid.Children.Add(MakeTeleCard("STARS (VS · DT)", tStars = MakeTeleVal("0/0 · 0/0", Theme.TextMain)));
            ugrid.Children.Add(MakeTeleCard("FRAGS (HP / DT)", tFrags = MakeTeleVal("0 / 0", Theme.TextMain)));
            ugrid.Children.Add(MakeTeleCard("TIMER · ENEMIES", tTimerEnemies = MakeTeleVal("0.0s · 0", Theme.TextMain)));

            return new Border
            {
                Background = Theme.BgPanel, BorderBrush = Theme.BorderSubtle, BorderThickness = new Thickness(0, 0, 0, 1),
                Padding = new Thickness(20, 10, 20, 10), Child = ugrid
            };
        }

        private UIElement BuildToolbar()
        {
            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var tabs = new WrapPanel { VerticalAlignment = VerticalAlignment.Center };
            string[][] defs = new string[][] {
                new[] { "all", "All Mods" }, new[] { "player", "Player" }, new[] { "combat", "Combat & Style" },
                new[] { "inventory", "Inventory & Keys" }, new[] { "movement", "Movement" },
                new[] { "world", "World & AI" }, new[] { "progression", "Camera & Teleport" }
            };
            foreach (var d in defs)
            {
                string cid = d[0];
                var btn = MakeFlatButton(d[1], Theme.BgCard, Brushes.Transparent, Theme.TextMuted);
                btn.FontSize = 11.5;
                btn.Padding = new Thickness(8, 4, 8, 4);
                btn.Margin = new Thickness(0, 2, 4, 2);
                btn.Click += delegate { activeCat = cid; RefreshTabHighlight(); ApplyVisibilityFilter(); };
                tabButtons[cid] = btn;
                tabs.Children.Add(btn);
            }
            RefreshTabHighlight();
            Grid.SetColumn(tabs, 0);
            grid.Children.Add(tabs);

            var right = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            right.Children.Add(new TextBlock
            {
                Text = "Presets:", FontSize = 11.5, FontWeight = FontWeights.SemiBold, Foreground = Theme.TextDim,
                VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(8, 0, 6, 0)
            });

            AddPresetBtn(right, "SSS God", "god_sss", Theme.CrimsonSoft, Theme.Brush("#66E11D48"), Theme.CrimsonText);
            AddPresetBtn(right, "Turbo Pro", "turbo_pro", Theme.CyanSoft, Theme.Brush("#6638BDF8"), Theme.CyanText);
            AddPresetBtn(right, "Fast Farm", "farm_fast", Theme.AmberSoft, Theme.Brush("#66F59E0B"), Theme.AmberText);

            var placeholder = MakeText("Search cheats or hotkeys...", 12, FontWeights.Normal, Theme.TextDim);
            placeholder.IsHitTestVisible = false;
            var searchBox = new TextBox
            {
                Background = Brushes.Transparent, BorderThickness = new Thickness(0),
                Foreground = Theme.TextMain, CaretBrush = Theme.Cyan, FontSize = 12,
                VerticalAlignment = VerticalAlignment.Center
            };
            searchBox.TextChanged += delegate
            {
                searchQuery = searchBox.Text ?? "";
                placeholder.Visibility = string.IsNullOrEmpty(searchQuery) ? Visibility.Visible : Visibility.Collapsed;
                ApplyVisibilityFilter();
            };
            var sGrid = new Grid();
            sGrid.Children.Add(placeholder);
            sGrid.Children.Add(searchBox);
            right.Children.Add(new Border
            {
                CornerRadius = new CornerRadius(7), Background = Theme.BgPanel, BorderBrush = Theme.BorderStrong,
                BorderThickness = new Thickness(1), Padding = new Thickness(8, 4, 8, 4), Width = 180,
                Margin = new Thickness(6, 0, 0, 0), Child = sGrid
            });

            Grid.SetColumn(right, 1);
            grid.Children.Add(right);

            return new Border
            {
                Background = Theme.BgRoot, BorderBrush = Theme.BorderSubtle, BorderThickness = new Thickness(0, 0, 0, 1),
                Padding = new Thickness(20, 10, 20, 10), Child = grid
            };
        }

        private void AddPresetBtn(StackPanel host, string text, string preset, Brush bg, Brush border, Brush fg)
        {
            var b = MakeFlatButton(text, bg, border, fg);
            b.Padding = new Thickness(9, 4, 9, 4);
            b.Margin = new Thickness(0, 0, 5, 0);
            b.Click += delegate { ipc.Send(Dict("cmd", "action", "action", "apply_preset", "payload", Dict("preset", preset))); };
            host.Children.Add(b);
        }

        private UIElement BuildFooter()
        {
            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            lastEventText = MakeText("Ready - click any hotkey badge to rebind (Backspace clears).", 12, FontWeights.Normal, Theme.TextMuted);
            Grid.SetColumn(lastEventText, 0);
            grid.Children.Add(lastEventText);

            var right = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            coordsText = MakeText("Pos: 0.0, 0.0, 0.0", 11.5, FontWeights.Normal, Theme.TextDim);
            coordsText.FontFamily = new FontFamily("Consolas");
            coordsText.Margin = new Thickness(0, 0, 16, 0);
            activeCountText = MakeText("0 Active", 12, FontWeights.Bold, Theme.CrimsonText);
            right.Children.Add(coordsText);
            right.Children.Add(activeCountText);
            Grid.SetColumn(right, 1);
            grid.Children.Add(right);

            return new Border
            {
                Background = Theme.BgPanel, BorderBrush = Theme.BorderSubtle, BorderThickness = new Thickness(0, 1, 0, 0),
                Padding = new Thickness(22, 7, 22, 7), Child = grid
            };
        }

        private void BuildCategoryCards()
        {
            categoriesHost.Children.Clear();
            rowMap.Clear();
            catMap.Clear();
            hkActionBtns.Clear();

            foreach (var cat in categories)
            {
                var card = new Border
                {
                    Background = Theme.BgCard, BorderBrush = Theme.BorderSubtle, BorderThickness = new Thickness(1),
                    CornerRadius = new CornerRadius(10), Margin = new Thickness(0, 0, 0, 14)
                };

                var hdrGrid = new Grid();
                hdrGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
                hdrGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

                var hdrLeft = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
                hdrLeft.Children.Add(new Border
                {
                    Width = 22, Height = 22, CornerRadius = new CornerRadius(5), Background = Theme.CyanSoft,
                    Margin = new Thickness(0, 0, 10, 0),
                    Child = MakeText(cat.Icon, 11.5, FontWeights.Bold, Theme.Cyan, HorizontalAlignment.Center)
                });
                hdrLeft.Children.Add(MakeText(cat.Title, 14, FontWeights.Bold, Theme.TextMain));

                var badgeTxt = MakeText(cat.Items.Count.ToString(), 11, FontWeights.SemiBold, Theme.TextMuted);
                var badgePill = new Border
                {
                    CornerRadius = new CornerRadius(9), Background = Theme.Brush("#242B3B"),
                    Padding = new Thickness(8, 1, 8, 1), Margin = new Thickness(10, 0, 0, 0),
                    VerticalAlignment = VerticalAlignment.Center, Child = badgeTxt
                };
                hdrLeft.Children.Add(badgePill);
                Grid.SetColumn(hdrLeft, 0);
                hdrGrid.Children.Add(hdrLeft);

                var chevron = MakeText("v", 12, FontWeights.Bold, Theme.TextDim);
                Grid.SetColumn(chevron, 1);
                hdrGrid.Children.Add(chevron);

                var hdrBorder = new Border
                {
                    Background = Theme.BgCardHdr, CornerRadius = new CornerRadius(10, 10, 0, 0),
                    BorderBrush = Theme.BorderSubtle, BorderThickness = new Thickness(0, 0, 0, 1),
                    Padding = new Thickness(14, 10, 14, 10), Cursor = Cursors.Hand, Child = hdrGrid
                };

                var bodyPanel = new StackPanel { Margin = new Thickness(8, 6, 8, 8) };
                var bodyWrap = new Border { Child = bodyPanel };
                var cref = new CatSectionRefs { Spec = cat, Card = card, BodyWrapper = bodyWrap, BadgePill = badgePill, BadgeText = badgeTxt, Chevron = chevron };
                catMap[cat.Id] = cref;

                hdrBorder.MouseLeftButtonUp += delegate
                {
                    cref.Collapsed = !cref.Collapsed;
                    cref.BodyWrapper.Visibility = cref.Collapsed ? Visibility.Collapsed : Visibility.Visible;
                    cref.Chevron.Text = cref.Collapsed ? ">" : "v";
                };

                if (cat.Actions.Count > 0)
                {
                    var actWrap = new WrapPanel { Margin = new Thickness(4, 2, 4, 8) };
                    foreach (var act in cat.Actions)
                    {
                        var cap = act;
                        var btn = MakeFlatButton(act.Label, act.Warn ? Theme.AmberSoft : Theme.CyanSoft,
                            act.Warn ? Theme.Brush("#66F59E0B") : Theme.Brush("#5538BDF8"),
                            act.Warn ? Theme.AmberText : Theme.CyanText);
                        btn.FontSize = 11.5;
                        btn.Padding = new Thickness(10, 4, 10, 4);
                        btn.Margin = new Thickness(0, 2, 6, 2);
                        btn.Click += delegate { HandleQuickAction(cap); };
                        actWrap.Children.Add(btn);
                    }
                    bodyPanel.Children.Add(actWrap);
                }

                foreach (var mod in cat.Items)
                {
                    var r = BuildModRow(mod);
                    rowMap[mod.Key] = r;
                    bodyPanel.Children.Add(r.RowBorder);
                }
                if (cat.HasTeleport) bodyPanel.Children.Add(BuildTeleportGrid());

                var stack = new StackPanel();
                stack.Children.Add(hdrBorder);
                stack.Children.Add(bodyWrap);
                card.Child = stack;
                categoriesHost.Children.Add(card);
            }
        }

        private ModRowRefs BuildModRow(ModSpec spec)
        {
            var r = new ModRowRefs { Spec = spec };
            var rowBorder = new Border
            {
                CornerRadius = new CornerRadius(7), Background = Brushes.Transparent,
                Padding = new Thickness(10, 7, 10, 7), Margin = new Thickness(0, 1, 0, 1)
            };
            r.RowBorder = rowBorder;
            rowBorder.MouseEnter += delegate { if (!r.Switch.IsOn) rowBorder.Background = Theme.BgRowHover; };
            rowBorder.MouseLeave += delegate { rowBorder.Background = r.Switch.IsOn ? Theme.BgRowActive : Brushes.Transparent; };

            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            for (int i = 0; i < 3; i++) grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var left = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            r.BoltIcon = MakeText("\u26A1", 12, FontWeights.Normal, Theme.Cyan, HorizontalAlignment.Center);
            r.BoltBox = new Border
            {
                Width = 24, Height = 24, CornerRadius = new CornerRadius(6),
                Background = Theme.Brush("#1F2636"), Margin = new Thickness(0, 0, 11, 0), Child = r.BoltIcon
            };
            left.Children.Add(r.BoltBox);
            var txtStack = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
            txtStack.Children.Add(MakeText(spec.Name, 13.5, FontWeights.SemiBold, Theme.TextMain));
            txtStack.Children.Add(MakeText(spec.Desc, 11.5, FontWeights.Normal, Theme.TextDim));
            left.Children.Add(txtStack);
            Grid.SetColumn(left, 0);
            grid.Children.Add(left);

            if (spec.Val != null)
            {
                var ctrlPanel = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(12, 0, 14, 0) };
                var vs = spec.Val;
                if (vs.ControlType == "range")
                {
                    var slider = new Slider
                    {
                        Width = 120, Minimum = vs.Min, Maximum = vs.Max, SmallChange = vs.Step, LargeChange = vs.Step * 2,
                        TickFrequency = vs.Step, IsSnapToTickEnabled = true, Style = darkSliderStyle
                    };
                    var valLbl = MakeText(FormatValLabel(vs.Min, vs.Suffix), 12, FontWeights.Bold, Theme.Cyan);
                    valLbl.Width = 56;
                    valLbl.TextAlignment = TextAlignment.Right;
                    valLbl.FontFamily = new FontFamily("Consolas");
                    valLbl.Margin = new Thickness(8, 0, 0, 0);

                    slider.AddHandler(Thumb.DragStartedEvent, new DragStartedEventHandler(delegate { r.IsSliderDragging = true; }));
                    slider.AddHandler(Thumb.DragCompletedEvent, new DragCompletedEventHandler(delegate
                    {
                        r.IsSliderDragging = false;
                        CommitSlider(vs.Key, slider.Value);
                    }));
                    slider.PreviewMouseLeftButtonUp += delegate { if (!r.IsSliderDragging) CommitSlider(vs.Key, slider.Value); };
                    slider.ValueChanged += delegate { valLbl.Text = FormatValLabel(Math.Round(slider.Value, 2), vs.Suffix); };

                    r.RangeSlider = slider;
                    r.RangeLabel = valLbl;
                    ctrlPanel.Children.Add(slider);
                    ctrlPanel.Children.Add(valLbl);
                }
                else
                {
                    var numBox = new TextBox
                    {
                        Width = 82, Background = Theme.BgInput, BorderBrush = Theme.BorderStrong, BorderThickness = new Thickness(1),
                        Foreground = Theme.TextMain, CaretBrush = Theme.Cyan, Padding = new Thickness(6, 3, 6, 3),
                        FontFamily = new FontFamily("Consolas"), FontSize = 12, TextAlignment = TextAlignment.Right,
                        VerticalAlignment = VerticalAlignment.Center
                    };
                    Action commitNum = delegate
                    {
                        long p;
                        if (long.TryParse(numBox.Text, out p))
                        {
                            long c = Math.Max((long)vs.Min, Math.Min((long)vs.Max, p));
                            localValues[vs.Key] = c;
                            numBox.Text = c.ToString(CultureInfo.InvariantCulture);
                            ipc.Send(Dict("cmd", "value", "key", vs.Key, "value", c));
                        }
                    };
                    numBox.KeyDown += delegate(object s, KeyEventArgs ke) { if (ke.Key == Key.Return) { commitNum(); Keyboard.ClearFocus(); } };
                    numBox.LostFocus += delegate { commitNum(); };
                    r.NumInput = numBox;
                    ctrlPanel.Children.Add(numBox);
                }
                Grid.SetColumn(ctrlPanel, 1);
                grid.Children.Add(ctrlPanel);
            }

            r.Switch = new SegSwitchControl { Margin = new Thickness(0, 0, 12, 0) };
            r.Switch.Toggled += delegate(bool nextState)
            {
                localToggles[spec.Key] = nextState;
                ApplyRowVisualState(r, nextState);
                UpdateCounters();
                ipc.Send(Dict("cmd", "toggle", "key", spec.Key, "state", nextState));
            };
            Grid.SetColumn(r.Switch, 2);
            grid.Children.Add(r.Switch);

            var hkBtn = MakeFlatButton("Bind", Theme.BgInput, Theme.BorderSubtle, Theme.TextDim);
            hkBtn.MinWidth = 74;
            hkBtn.FontFamily = new FontFamily("Consolas");
            hkBtn.FontSize = 11.5;
            hkBtn.Padding = new Thickness(8, 4, 8, 4);
            hkBtn.Click += delegate { OpenHotkeyModal(spec.Key, spec.Name); };
            r.HotkeyBtn = hkBtn;
            hkActionBtns[spec.Key] = hkBtn;
            Grid.SetColumn(hkBtn, 3);
            grid.Children.Add(hkBtn);

            rowBorder.Child = grid;
            return r;
        }

        private void CommitSlider(string key, double rawVal)
        {
            double v = Math.Round(rawVal, 3);
            localValues[key] = v;
            ipc.Send(Dict("cmd", "value", "key", key, "value", v));
        }

        private UIElement BuildTeleportGrid()
        {
            var ugrid = new UniformGrid { Columns = 3 };
            for (int i = 0; i < 3; i++)
            {
                int slotIdx = i;
                var stack = new StackPanel();
                var head = new Grid();
                head.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
                head.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
                var title = MakeText("Location Slot " + (slotIdx + 1), 12, FontWeights.Bold, Theme.TextMain);
                Grid.SetColumn(title, 0);
                head.Children.Add(title);

                if (slotIdx == 0)
                {
                    var hkPair = new StackPanel { Orientation = Orientation.Horizontal };
                    var bSaveHk = MakeMiniHkBtn("Num.", "save_pos_0", "Save Location Slot 1", new Thickness(0, 0, 4, 0));
                    var bLoadHk = MakeMiniHkBtn("Num+", "load_pos_0", "Teleport to Slot 1", new Thickness(0));
                    hkPair.Children.Add(bSaveHk);
                    hkPair.Children.Add(bLoadHk);
                    Grid.SetColumn(hkPair, 1);
                    head.Children.Add(hkPair);
                }
                stack.Children.Add(head);

                tpSlotCoords[slotIdx] = MakeText("Empty", 11, FontWeights.Normal, Theme.TextMuted);
                tpSlotCoords[slotIdx].FontFamily = new FontFamily("Consolas");
                tpSlotCoords[slotIdx].Margin = new Thickness(0, 5, 0, 7);
                stack.Children.Add(tpSlotCoords[slotIdx]);

                var btns = new UniformGrid { Columns = (slotIdx == 0 ? 3 : 2) };
                var bSave = MakeFlatButton("Save", Theme.CyanSoft, Theme.Brush("#5538BDF8"), Theme.CyanText);
                bSave.FontSize = 11.5; bSave.Padding = new Thickness(6, 4, 6, 4); bSave.Margin = new Thickness(0, 0, 4, 0);
                bSave.Click += delegate { ipc.Send(Dict("cmd", "action", "action", "save_pos", "payload", Dict("slot", slotIdx))); };
                btns.Children.Add(bSave);

                var bTele = MakeFlatButton("Teleport", Theme.CyanSoft, Theme.Brush("#5538BDF8"), Theme.CyanText);
                bTele.FontSize = 11.5; bTele.Padding = new Thickness(6, 4, 6, 4);
                if (slotIdx == 0) bTele.Margin = new Thickness(0, 0, 4, 0);
                bTele.Click += delegate { ipc.Send(Dict("cmd", "action", "action", "load_pos", "payload", Dict("slot", slotIdx))); };
                btns.Children.Add(bTele);

                if (slotIdx == 0)
                {
                    var bUndo = MakeFlatButton("Undo", Theme.BgCard, Theme.BorderStrong, Theme.TextMain);
                    bUndo.FontSize = 11.5; bUndo.Padding = new Thickness(6, 4, 6, 4);
                    bUndo.Click += delegate { ipc.Send(Dict("cmd", "action", "action", "undo_teleport")); };
                    btns.Children.Add(bUndo);
                }
                stack.Children.Add(btns);
                ugrid.Children.Add(new Border
                {
                    Background = Theme.BgInput, BorderBrush = Theme.BorderSubtle, BorderThickness = new Thickness(1),
                    CornerRadius = new CornerRadius(8), Padding = new Thickness(10, 8, 10, 8), Margin = new Thickness(4), Child = stack
                });
            }

            return new Border
            {
                BorderBrush = Theme.BorderSubtle, BorderThickness = new Thickness(0, 1, 0, 0),
                Margin = new Thickness(4, 8, 4, 0), Padding = new Thickness(0, 10, 0, 2), Child = ugrid
            };
        }

        private Button MakeMiniHkBtn(string init, string action, string label, Thickness margin)
        {
            var b = MakeFlatButton(init, Theme.BgCard, Theme.BorderSubtle, Theme.TextMuted);
            b.FontFamily = new FontFamily("Consolas");
            b.FontSize = 10.5;
            b.Padding = new Thickness(6, 2, 6, 2);
            b.Margin = margin;
            b.Click += delegate { OpenHotkeyModal(action, label); };
            hkActionBtns[action] = b;
            return b;
        }

        private Grid BuildHotkeyModal()
        {
            var overlay = new Grid { Background = Theme.Brush("#B8000000"), Visibility = Visibility.Collapsed };
            var stack = new StackPanel();
            stack.Children.Add(MakeText("Bind Global Hotkey", 16, FontWeights.Bold, Theme.TextMain, HorizontalAlignment.Center));
            hotkeyTargetLabel = MakeText("", 13, FontWeights.SemiBold, Theme.Cyan, HorizontalAlignment.Center);
            hotkeyTargetLabel.Margin = new Thickness(0, 4, 0, 12);
            stack.Children.Add(hotkeyTargetLabel);

            stack.Children.Add(new Border
            {
                Background = Theme.BgInput, BorderBrush = Theme.Cyan, BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(8), Padding = new Thickness(12, 16, 12, 16), Margin = new Thickness(0, 0, 0, 14),
                Child = new TextBlock
                {
                    Text = "Press any key combination\n(F1-F12, Num0-Num9, Ctrl+F1, Alt+G...)",
                    FontSize = 12, Foreground = Theme.TextMuted, TextAlignment = TextAlignment.Center
                }
            });

            var actions = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Center };
            var clearBtn = MakeFlatButton("Clear Hotkey", Theme.BgPanel, Theme.BorderStrong, Theme.TextMain);
            clearBtn.Margin = new Thickness(0, 0, 10, 0);
            clearBtn.Click += delegate { SaveHotkey(""); };
            var cancelBtn = MakeFlatButton("Cancel (Esc)", Theme.BgPanel, Theme.BorderStrong, Theme.TextMain);
            cancelBtn.Click += delegate { CloseHotkeyModal(); };
            actions.Children.Add(clearBtn);
            actions.Children.Add(cancelBtn);
            stack.Children.Add(actions);

            overlay.Children.Add(new Border
            {
                Width = 400, Background = Theme.BgCard, BorderBrush = Theme.BorderStrong, BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(12), Padding = new Thickness(22),
                HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center, Child = stack
            });
            return overlay;
        }

        private void OpenHotkeyModal(string action, string label)
        {
            bindingAction = action;
            hotkeyTargetLabel.Text = label;
            hotkeyModalOverlay.Visibility = Visibility.Visible;
        }

        private void CloseHotkeyModal()
        {
            bindingAction = null;
            hotkeyModalOverlay.Visibility = Visibility.Collapsed;
        }

        private void SaveHotkey(string hk)
        {
            if (string.IsNullOrEmpty(bindingAction)) return;
            string act = bindingAction;
            localHotkeys[act] = hk;
            CloseHotkeyModal();
            RefreshHotkeyButtons();
            ipc.Send(Dict("cmd", "hotkey", "action", act, "hotkey", hk));
        }

        private void OnWindowPreviewKeyDown(object sender, KeyEventArgs e)
        {
            if (string.IsNullOrEmpty(bindingAction)) return;
            e.Handled = true;
            if (e.Key == Key.Escape) { CloseHotkeyModal(); return; }
            if (e.Key == Key.Back) { SaveHotkey(""); return; }
            string combo = TrainerCatalog.MapWpfKeyToHotkey(e.Key == Key.System ? e.SystemKey : e.Key, Keyboard.Modifiers);
            if (!string.IsNullOrEmpty(combo)) SaveHotkey(combo);
        }

        private void HandleQuickAction(ActionSpec act)
        {
            if (act.Action == "batch_keys_99")
            {
                foreach (var k in new[] { "MundusKeyBronze", "MundusKeySilver", "MundusKeyGold", "MundusKeyIvory" })
                    ipc.Send(Dict("cmd", "action", "action", "set_stat", "payload", Dict("name", k, "value", 99)));
                return;
            }
            if (act.Action == "batch_stars_10")
            {
                foreach (var s in new[] { "VitalStar_Small", "VitalStar_Large", "DevilTriggerStar_Small", "DevilTriggerStar_Large" })
                    ipc.Send(Dict("cmd", "action", "action", "set_stat", "payload", Dict("name", s, "value", 10)));
                return;
            }
            ipc.Send(Dict("cmd", "action", "action", act.Action, "payload", act.Payload ?? new Dictionary<string, object>()));
        }

        private void ApplyServerState(Dictionary<string, object> state)
        {
            var tele = state["telemetry"] as Dictionary<string, object>;
            var toggles = state["toggles"] as Dictionary<string, object>;
            var values = state["values"] as Dictionary<string, object>;
            var hotkeys = state["hotkeys"] as Dictionary<string, object>;

            if (state.ContainsKey("sound_feedback"))
            {
                localSound = ToBool(state["sound_feedback"]);
                UpdateSoundButtonVisual();
            }

            if (toggles != null)
            {
                foreach (var kv in toggles)
                {
                    bool on = ToBool(kv.Value);
                    localToggles[kv.Key] = on;
                    ModRowRefs r;
                    if (rowMap.TryGetValue(kv.Key, out r))
                    {
                        r.Switch.SetVisualState(on);
                        ApplyRowVisualState(r, on);
                    }
                }
            }

            if (values != null)
            {
                foreach (var kv in values) localValues[kv.Key] = ToDouble(kv.Value);
                foreach (var r in rowMap.Values)
                {
                    if (r.Spec.Val == null) continue;
                    double dv;
                    if (!localValues.TryGetValue(r.Spec.Val.Key, out dv)) continue;
                    if (r.RangeSlider != null && !r.IsSliderDragging)
                    {
                        r.RangeSlider.Value = dv;
                        r.RangeLabel.Text = FormatValLabel(dv, r.Spec.Val.Suffix);
                    }
                    else if (r.NumInput != null && !r.NumInput.IsKeyboardFocused)
                    {
                        r.NumInput.Text = ((long)Math.Round(dv)).ToString(CultureInfo.InvariantCulture);
                    }
                }
            }

            if (hotkeys != null)
            {
                foreach (var kv in hotkeys) localHotkeys[kv.Key] = (kv.Value != null) ? kv.Value.ToString() : "";
                RefreshHotkeyButtons();
            }

            if (tele != null)
            {
                bool attached = ToBool(GetVal(tele, "attached"));
                bool inGame = ToBool(GetVal(tele, "in_game"));
                string ch = (GetVal(tele, "character") ?? "").ToString();

                connDot.Fill = attached ? Theme.Green : Theme.Amber;
                connText.Text = attached
                    ? string.Format("Attached · PID {0}{1}", ToLong(GetVal(tele, "pid")), inGame ? "" : " (Menus / Loading)")
                    : "Waiting for DMC-DevilMayCry.exe...";

                charText.Text = ch;
                charPill.Visibility = (attached && !string.IsNullOrEmpty(ch) && ch != "None") ? Visibility.Visible : Visibility.Collapsed;
                hookText.Text = ToBool(GetVal(state, "counter_dec_available")) ? "CounterDec Hook Ready" : "External Hook Detected (Safe Yield)";
                hookPill.Visibility = attached ? Visibility.Visible : Visibility.Collapsed;

                int rank = (int)Math.Max(0, Math.Min(7, ToLong(GetVal(tele, "style_rank"))));
                tStyleRank.Text = TrainerCatalog.StyleRankNames[rank];
                tStyleRank.Foreground = rank == 0 ? Theme.TextDim : (rank <= 2 ? Theme.TextMuted : (rank <= 4 ? Theme.Cyan : (rank <= 6 ? Theme.Amber : Theme.Crimson)));
                tStylePts.Text = Math.Round(ToDouble(GetVal(tele, "style_points"))).ToString("N0");

                tHp.Text = string.Format("{0} / {1}", Math.Round(ToDouble(GetVal(tele, "health"))), Math.Round(ToDouble(GetVal(tele, "max_health"))));
                tDt.Text = string.Format("{0} / {1}", Math.Round(ToDouble(GetVal(tele, "devil_trigger"))), Math.Round(ToDouble(GetVal(tele, "max_devil_trigger"))));
                tOd.Text = string.Format("{0} / {1}", Math.Round(ToDouble(GetVal(tele, "overdrive"))), Math.Round(ToDouble(GetVal(tele, "max_overdrive"))));
                tRedOrbs.Text = ToLong(GetVal(tele, "red_orbs")).ToString("N0");
                tGoldUp.Text = string.Format("{0} · {1} pt", ToLong(GetVal(tele, "gold_orbs")), ToLong(GetVal(tele, "upgrade_points")));
                tKeys.Text = string.Format("{0} / {1} / {2} / {3}", ToLong(GetVal(tele, "copper_keys")), ToLong(GetVal(tele, "argent_keys")), ToLong(GetVal(tele, "gold_keys")), ToLong(GetVal(tele, "ivory_keys")));
                tStars.Text = string.Format("{0}/{1} · {2}/{3}", ToLong(GetVal(tele, "small_vs")), ToLong(GetVal(tele, "large_vs")), ToLong(GetVal(tele, "small_dts")), ToLong(GetVal(tele, "large_dts")));
                tFrags.Text = string.Format("{0} / {1}", ToLong(GetVal(tele, "blue_frags")), ToLong(GetVal(tele, "purple_frags")));
                tTimerEnemies.Text = string.Format("{0:0.0}s · {1}", ToDouble(GetVal(tele, "mission_time")), ToLong(GetVal(tele, "active_enemies")));

                var locArr = GetVal(tele, "location") as ArrayList;
                if (locArr != null && locArr.Count >= 3)
                    coordsText.Text = string.Format("Pos: {0:0.0}, {1:0.0}, {2:0.0}", ToDouble(locArr[0]), ToDouble(locArr[1]), ToDouble(locArr[2]));

                string ev = (GetVal(tele, "last_event") ?? "").ToString();
                if (!string.IsNullOrEmpty(ev)) lastEventText.Text = ev;

                var slots = GetVal(tele, "saved_slots") as ArrayList;
                if (slots != null)
                {
                    for (int i = 0; i < 3 && i < slots.Count; i++)
                    {
                        var sc = slots[i] as ArrayList;
                        tpSlotCoords[i].Text = (sc != null && sc.Count >= 3) ? string.Format("{0}, {1}, {2}", sc[0], sc[1], sc[2]) : "Empty";
                    }
                }
            }
            UpdateCounters();
        }

        private void ApplyRowVisualState(ModRowRefs r, bool on)
        {
            r.RowBorder.Background = on ? Theme.BgRowActive : (r.RowBorder.IsMouseOver ? Theme.BgRowHover : Brushes.Transparent);
            r.BoltBox.Background = on ? Theme.CrimsonSoft : Theme.Brush("#1F2636");
            r.BoltIcon.Foreground = on ? Theme.CrimsonText : Theme.Cyan;
        }

        private void UpdateCounters()
        {
            int total = 0;
            foreach (var v in localToggles.Values) if (v) total++;
            activeCountText.Text = total + " Active";
            foreach (var cat in categories)
            {
                var cref = catMap[cat.Id];
                int active = 0;
                foreach (var mod in cat.Items) { bool on; if (localToggles.TryGetValue(mod.Key, out on) && on) active++; }
                cref.BadgeText.Text = active > 0 ? string.Format("{0} / {1} active", active, cat.Items.Count) : cat.Items.Count.ToString();
                cref.BadgePill.Background = active > 0 ? Theme.CrimsonSoft : Theme.Brush("#242B3B");
                cref.BadgeText.Foreground = active > 0 ? Theme.CrimsonText : Theme.TextMuted;
            }
        }

        private void RefreshHotkeyButtons()
        {
            foreach (var kv in hkActionBtns)
            {
                string hk; localHotkeys.TryGetValue(kv.Key, out hk);
                bool empty = string.IsNullOrEmpty(hk);
                kv.Value.Content = empty ? "Bind" : hk.Replace("+", " ");
                kv.Value.Foreground = empty ? Theme.TextDim : Theme.TextMuted;
            }
        }

        private void UpdateSoundButtonVisual()
        {
            soundBtn.Content = localSound ? "Sound On" : "Sound Off";
            soundBtn.Background = localSound ? Theme.CyanSoft : Theme.BgCard;
            soundBtn.BorderBrush = localSound ? Theme.Brush("#6638BDF8") : Theme.BorderStrong;
            soundBtn.Foreground = localSound ? Theme.TextMain : Theme.TextMuted;
        }

        private void RefreshTabHighlight()
        {
            foreach (var kv in tabButtons)
            {
                bool active = (kv.Key == activeCat);
                kv.Value.Background = active ? Theme.CrimsonSoft : Theme.BgCard;
                kv.Value.BorderBrush = active ? Theme.Brush("#77E11D48") : Brushes.Transparent;
                kv.Value.Foreground = active ? Theme.White : Theme.TextMuted;
            }
        }

        private void ApplyVisibilityFilter()
        {
            string q = searchQuery.Trim().ToLowerInvariant();
            foreach (var cat in categories)
            {
                var cref = catMap[cat.Id];
                if (activeCat != "all" && activeCat != cat.Id) { cref.Card.Visibility = Visibility.Collapsed; continue; }
                int vis = 0;
                foreach (var mod in cat.Items)
                {
                    var r = rowMap[mod.Key];
                    string hk; localHotkeys.TryGetValue(mod.Key, out hk);
                    bool match = string.IsNullOrEmpty(q) || mod.Name.ToLowerInvariant().Contains(q) ||
                                 mod.Desc.ToLowerInvariant().Contains(q) || (!string.IsNullOrEmpty(hk) && hk.ToLowerInvariant().Contains(q));
                    r.RowBorder.Visibility = match ? Visibility.Visible : Visibility.Collapsed;
                    if (match) vis++;
                }
                cref.Card.Visibility = (vis > 0 || (string.IsNullOrEmpty(q) && cat.HasTeleport)) ? Visibility.Visible : Visibility.Collapsed;
            }
        }

        // UI & Conversion Helpers
        private static TextBlock MakeText(string text, double size, FontWeight weight, Brush fg, HorizontalAlignment ha = HorizontalAlignment.Left)
        {
            return new TextBlock { Text = text, FontSize = size, FontWeight = weight, Foreground = fg, HorizontalAlignment = ha, VerticalAlignment = VerticalAlignment.Center };
        }

        private static TextBlock MakeTeleVal(string init, Brush color) { return MakeText(init, 13, FontWeights.Bold, color); }

        private static Border MakeTeleCard(string label, UIElement content)
        {
            var stack = new StackPanel();
            var lbl = MakeText(label, 10, FontWeights.SemiBold, Theme.TextDim);
            lbl.Margin = new Thickness(0, 0, 0, 2);
            stack.Children.Add(lbl);
            stack.Children.Add(content);
            return new Border
            {
                Background = Theme.Brush("#151A25"), BorderBrush = Theme.BorderSubtle, BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(7), Padding = new Thickness(10, 6, 10, 6), Margin = new Thickness(3), Child = stack
            };
        }

        private static Border MakePill(string text, Brush bg, Brush border, Brush fg, Thickness margin)
        {
            return new Border
            {
                CornerRadius = new CornerRadius(10), Background = bg, BorderBrush = border, BorderThickness = new Thickness(1),
                Padding = new Thickness(8, 2, 8, 2), Margin = margin, VerticalAlignment = VerticalAlignment.Center,
                Child = MakeText(text, 11, FontWeights.SemiBold, fg)
            };
        }

        private static Border WrapPill(TextBlock child, Brush bg, Thickness margin)
        {
            return new Border
            {
                CornerRadius = new CornerRadius(9), Background = bg, Padding = new Thickness(8, 1, 8, 1),
                Margin = margin, Visibility = Visibility.Collapsed, Child = child
            };
        }

        private static Button MakeFlatButton(string text, Brush bg, Brush border, Brush fg)
        {
            var template = new ControlTemplate(typeof(Button));
            var bd = new FrameworkElementFactory(typeof(Border));
            bd.SetValue(Border.BackgroundProperty, new TemplateBindingExtension(Button.BackgroundProperty));
            bd.SetValue(Border.BorderBrushProperty, new TemplateBindingExtension(Button.BorderBrushProperty));
            bd.SetValue(Border.BorderThicknessProperty, new Thickness(1));
            bd.SetValue(Border.CornerRadiusProperty, new CornerRadius(7));
            bd.SetValue(Border.PaddingProperty, new TemplateBindingExtension(Button.PaddingProperty));
            var cp = new FrameworkElementFactory(typeof(ContentPresenter));
            cp.SetValue(ContentPresenter.HorizontalAlignmentProperty, HorizontalAlignment.Center);
            cp.SetValue(ContentPresenter.VerticalAlignmentProperty, VerticalAlignment.Center);
            bd.AppendChild(cp);
            template.VisualTree = bd;
            return new Button
            {
                Content = text, Background = bg, BorderBrush = border, Foreground = fg,
                FontSize = 12, FontWeight = FontWeights.SemiBold, Padding = new Thickness(11, 5, 11, 5),
                Cursor = Cursors.Hand, Focusable = false, Template = template
            };
        }

        private static string FormatValLabel(double v, string suffix)
        {
            return (Math.Abs(v - Math.Round(v)) < 0.001 ? ((long)Math.Round(v)).ToString() : v.ToString("0.##", CultureInfo.InvariantCulture)) + (suffix ?? "");
        }

        private static Dictionary<string, object> Dict(params object[] kv)
        {
            var d = new Dictionary<string, object>();
            for (int i = 0; i + 1 < kv.Length; i += 2) d[kv[i].ToString()] = kv[i + 1];
            return d;
        }

        private static object GetVal(Dictionary<string, object> d, string k) { object v; return (d != null && d.TryGetValue(k, out v)) ? v : null; }
        private static bool ToBool(object o) { return (o is bool) && (bool)o; }
        private static long ToLong(object o) { if (o == null) return 0; try { return Convert.ToInt64(o); } catch { return 0; } }
        private static double ToDouble(object o) { if (o == null) return 0.0; try { return Convert.ToDouble(o, CultureInfo.InvariantCulture); } catch { return 0.0; } }
    }

    internal static class Program
    {
        private static string FindPythonExe()
        {
            string pathEnv = Environment.GetEnvironmentVariable("PATH") ?? "";
            foreach (string rawDir in pathEnv.Split(System.IO.Path.PathSeparator))
            {
                string dir = rawDir.Trim().Trim('"');
                if (string.IsNullOrEmpty(dir)) continue;
                string py = System.IO.Path.Combine(dir, "python.exe");
                if (File.Exists(py)) return py;
            }
            string pyRoot = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python");
            if (Directory.Exists(pyRoot))
            {
                foreach (string sub in Directory.GetDirectories(pyRoot, "Python*"))
                {
                    string py = System.IO.Path.Combine(sub, "python.exe");
                    if (File.Exists(py)) return py;
                }
            }
            return null;
        }

        [STAThread]
        private static void Main()
        {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string backendPy = System.IO.Path.Combine(baseDir, "trainer_backend.py");
            if (!File.Exists(backendPy))
            {
                MessageBox.Show("Could not find trainer_backend.py next to DmC_Trainer.exe.", "DmC Trainer", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }
            string pyExe = FindPythonExe();
            if (string.IsNullOrEmpty(pyExe))
            {
                MessageBox.Show("Python 3 (python.exe) was not found in PATH or LocalAppData.", "DmC Trainer", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            Process proc = null;
            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = pyExe,
                    Arguments = string.Format("-u \"{0}\" --ipc", backendPy),
                    WorkingDirectory = baseDir,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardInput = true,
                    RedirectStandardOutput = true,
                    StandardOutputEncoding = Encoding.UTF8
                };
                proc = Process.Start(psi);

                var app = new Application();
                app.DispatcherUnhandledException += delegate(object s, System.Windows.Threading.DispatcherUnhandledExceptionEventArgs args)
                {
                    MessageBox.Show("UI Error:\n" + args.Exception.Message, "DmC Trainer", MessageBoxButton.OK, MessageBoxImage.Error);
                    args.Handled = true;
                };
                var win = new TrainerWindow(new IpcClient(proc), proc);
                app.Run(win);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Startup failed:\n" + ex.ToString(), "DmC Trainer", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                try { if (proc != null && !proc.HasExited) proc.Kill(); }
                catch { }
            }
        }
    }
}
