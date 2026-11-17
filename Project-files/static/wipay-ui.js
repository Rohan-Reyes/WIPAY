/* Shared progressive enhancements. All essential forms work without this file. */
function navigateTo(name) {
  const item = Array.from(document.querySelectorAll('.nav-item')).find(nav =>
    nav.getAttribute('onclick') === `showPage('${name}',this)`);
  if (item) showPage(name, item);
}

document.addEventListener('DOMContentLoaded', () => {
  const tabs = Array.from(document.querySelectorAll('.tab-btn'));
  const tabNames = ['type', 'scan', 'request', 'history'];
  tabs.forEach((tab, index) => {
    const panel = document.getElementById('tab-' + tabNames[index]);
    tab.id = 'connect-' + tabNames[index];
    tab.setAttribute('role', 'tab');
    tab.setAttribute('aria-controls', panel.id);
    panel.setAttribute('role', 'tabpanel');
    panel.setAttribute('aria-labelledby', tab.id);
    panel.tabIndex = 0;
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next === undefined) return;
      event.preventDefault();
      tabs[next].click();
      tabs[next].focus();
    });
  });
  function syncTabs() {
    tabs.forEach(tab => {
      const selected = tab.classList.contains('active');
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
    });
  }
  if (tabs.length) {
    new MutationObserver(syncTabs).observe(document.querySelector('.tabs'), {
      attributes: true, subtree: true, attributeFilter: ['class']
    });
    syncTabs();
    // Bring returning customers directly to the result of their access request.
    if (document.querySelector('#tab-request .lobby-confirm')) tabs[2].click();
  }

  const sidebar = document.getElementById('sidebar');
  const menu = document.querySelector('.topbar-hamburger');
  if (sidebar && menu) {
    function syncDrawer() {
      const mobile = window.innerWidth < 768;
      const open = sidebar.classList.contains('open');
      sidebar.inert = mobile && !open;
      menu.setAttribute('aria-expanded', String(open));
      menu.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    }
    new MutationObserver(syncDrawer).observe(sidebar, { attributes: true, attributeFilter: ['class'] });
    menu.addEventListener('click', () => {
      syncDrawer();
      if (sidebar.classList.contains('open')) sidebar.querySelector('.nav-item').focus();
    });
    sidebar.addEventListener('keydown', event => {
      if (window.innerWidth >= 768 || event.key !== 'Tab') return;
      const items = Array.from(sidebar.querySelectorAll('button, a[href]'));
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault(); last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first.focus();
      }
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && sidebar.classList.contains('open')) {
        closeSidebar(); menu.focus();
      }
    });
    sidebar.querySelectorAll('.nav-item').forEach(item => item.addEventListener('click', () => {
      if (window.innerWidth < 768) document.getElementById('main-content').focus();
    }));
    window.addEventListener('resize', () => {
      if (window.innerWidth >= 768) closeSidebar();
      syncDrawer();
    });
    syncDrawer();
    window.addEventListener('hashchange', () => navigateTo(location.hash.slice(1)));
  }
});
