document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide Icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Sidebar Toggle
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }

    // Dark Mode Toggle
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    
    // Check local storage for theme
    const currentTheme = localStorage.getItem('theme');
    const updateThemeIcon = () => {
        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            if (icon) {
                if (body.classList.contains('dark-mode')) {
                    icon.setAttribute('data-lucide', 'sun');
                } else {
                    icon.setAttribute('data-lucide', 'moon');
                }
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
        }
    };

    if (currentTheme === 'dark') {
        body.classList.add('dark-mode');
    }
    updateThemeIcon();

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            
            let theme = 'light';
            if (body.classList.contains('dark-mode')) {
                theme = 'dark';
            }
            localStorage.setItem('theme', theme);
            updateThemeIcon();
        });
    }

    // Command Palette (Ctrl+K)
    const commandPalette = document.getElementById('command-palette');
    
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            if (commandPalette) {
                commandPalette.classList.toggle('active');
                if (commandPalette.classList.contains('active')) {
                    const searchInput = commandPalette.querySelector('input');
                    if (searchInput) searchInput.focus();
                }
            }
        }
        
        // Close with Escape
        if (e.key === 'Escape' && commandPalette && commandPalette.classList.contains('active')) {
            commandPalette.classList.remove('active');
        }
    });

    // Close command palette when clicking outside
    if (commandPalette) {
        commandPalette.addEventListener('click', (e) => {
            if (e.target === commandPalette) {
                commandPalette.classList.remove('active');
            }
        });
    }

    // Quick Preview Drawer Toggle
    const previewDrawer = document.getElementById('preview-drawer');
    const drawerToggles = document.querySelectorAll('.preview-toggle');
    const closeDrawer = document.getElementById('close-drawer');

    if (previewDrawer) {
        drawerToggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                previewDrawer.classList.add('open');
            });
        });

        if (closeDrawer) {
            closeDrawer.addEventListener('click', () => {
                previewDrawer.classList.remove('open');
            });
        }
    }

    // Profile Dropdown Logic
    const profileTrigger = document.getElementById('profile-dropdown-trigger');
    const profileDropdown = document.getElementById('profile-dropdown');

    if (profileTrigger && profileDropdown) {
        profileTrigger.addEventListener('click', (e) => {
            // Prevent event from bubbling up to document
            e.stopPropagation();
            profileDropdown.classList.toggle('show');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!profileTrigger.contains(e.target)) {
                profileDropdown.classList.remove('show');
            }
        });
    }

    // Tab Switching Logic
    const tabContents = document.querySelectorAll('.tab-content');
    const tabLinks = document.querySelectorAll('.tab-link');

    tabLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('data-tab');
            
            // Remove active class from all links and contents
            tabLinks.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked link and target content
            link.classList.add('active');
            const targetContent = document.getElementById(targetId);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
});
