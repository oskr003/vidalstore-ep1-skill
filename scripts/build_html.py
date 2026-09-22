import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_all_defense_docs import DIALOGUES

HTML_PATH_D6 = "/Users/oscar/Downloads/DUOC/CloudNative/Evaluacion 1/Guia_Defensa_VidalStore_EP1_D6.html"
HTML_PATH_MAIN = "/Users/oscar/Downloads/DUOC/CloudNative/Evaluacion 1/Guia_Defensa_VidalStore_EP1.html"

TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="theme-color" content="#0A0E17">
  <title>Simulador y Guía de Defensa Técnica EP1 · VidalStore (D6)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-main: #0A0E17;
      --bg-surface: #111827;
      --bg-surface-elevated: #162032;
      --bg-card: rgba(22, 32, 50, 0.85);
      --border-subtle: #1F293D;
      --border-focus: #38BDF8;
      --text-primary: #F8FAFC;
      --text-secondary: #94A3B8;
      --text-muted: #64748B;
      
      --accent-cyan: #06B6D4;
      --accent-blue: #38BDF8;
      --accent-indigo: #6366F1;
      --accent-emerald: #10B981;
      --accent-rose: #F43F5E;
      --accent-amber: #F59E0B;
      --accent-purple: #A855F7;

      --font-display: 'Outfit', -apple-system, sans-serif;
      --font-body: 'Inter', -apple-system, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;

      --radius-sm: 8px;
      --radius-md: 12px;
      --radius-lg: 16px;
      --radius-xl: 22px;
      --shadow-glow: 0 0 25px rgba(56, 189, 248, 0.15);
      --shadow-card: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
    }

    body {
      background-color: var(--bg-main);
      color: var(--text-primary);
      font-family: var(--font-body);
      line-height: 1.6;
      background-image: 
        radial-gradient(circle at 15% 15%, rgba(14, 165, 233, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 85% 85%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
        linear-gradient(180deg, #0A0E17 0%, #06090F 100%);
      min-height: 100vh;
      overflow-x: hidden;
      padding-bottom: env(safe-area-inset-bottom);
    }

    /* Top Sticky Header */
    .top-bar {
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(10, 14, 23, 0.92);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border-subtle);
      padding: 0.65rem 1.5rem;
      padding-top: max(0.65rem, env(safe-area-inset-top));
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
    }

    .brand-group {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      min-width: 0;
    }

    .brand-badge {
      background: linear-gradient(135deg, #0284C7, #6366F1);
      color: #fff;
      font-family: var(--font-display);
      font-weight: 800;
      font-size: 0.78rem;
      padding: 0.2rem 0.5rem;
      border-radius: var(--radius-sm);
      letter-spacing: 0.5px;
      flex-shrink: 0;
    }

    .brand-title {
      font-family: var(--font-display);
      font-weight: 700;
      font-size: 1.05rem;
      background: linear-gradient(135deg, #F8FAFC 30%, #94A3B8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .nav-stats {
      display: flex;
      gap: 0.5rem;
      flex-shrink: 0;
    }

    .stat-chip {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      color: var(--text-secondary);
      display: flex;
      align-items: center;
      gap: 0.35rem;
      white-space: nowrap;
    }

    .stat-chip strong {
      color: var(--accent-blue);
    }

    /* Floating Mini-Timer Pill on Scroll (Mobile & Desktop) */
    .sticky-mini-timer {
      position: fixed;
      top: 4.2rem;
      right: 1rem;
      background: rgba(15, 23, 42, 0.92);
      border: 1px solid rgba(56, 189, 248, 0.4);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-radius: 9999px;
      padding: 0.35rem 0.85rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-family: var(--font-mono);
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--accent-cyan);
      box-shadow: 0 4px 20px rgba(0,0,0,0.4);
      z-index: 95;
      transform: translateY(-80px);
      opacity: 0;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      cursor: pointer;
    }

    .sticky-mini-timer.visible {
      transform: translateY(0);
      opacity: 1;
    }

    .sticky-mini-timer.danger {
      color: var(--accent-rose);
      border-color: var(--accent-rose);
      animation: pulse 1s infinite;
    }

    /* Main Container */
    .container {
      max-width: 1280px;
      margin: 0 auto;
      padding: 1.5rem;
    }

    /* Hero Section */
    .hero {
      background: linear-gradient(180deg, rgba(22, 32, 50, 0.65) 0%, rgba(17, 24, 39, 0.5) 100%);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-xl);
      padding: 2rem;
      margin-bottom: 1.75rem;
      position: relative;
      overflow: hidden;
      box-shadow: var(--shadow-card);
    }

    .hero-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-bottom: 0.85rem;
    }

    .tag {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.2rem 0.55rem;
      border-radius: var(--radius-sm);
      font-size: 0.72rem;
      font-weight: 600;
      letter-spacing: 0.3px;
    }

    .tag-blue { background: rgba(56, 189, 248, 0.15); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.3); }
    .tag-green { background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .tag-purple { background: rgba(168, 85, 247, 0.15); color: #C084FC; border: 1px solid rgba(168, 85, 247, 0.3); }
    .tag-rose { background: rgba(244, 63, 94, 0.15); color: #FB7185; border: 1px solid rgba(244, 63, 94, 0.3); }

    .hero h1 {
      font-family: var(--font-display);
      font-size: 2.1rem;
      font-weight: 800;
      line-height: 1.2;
      margin-bottom: 0.75rem;
      letter-spacing: -0.5px;
    }

    .hero p {
      color: var(--text-secondary);
      font-size: 0.98rem;
      max-width: 860px;
      margin-bottom: 1.5rem;
      line-height: 1.5;
    }

    /* Timer Widget */
    .timer-widget {
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: var(--radius-lg);
      padding: 1.25rem 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1.25rem;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    .timer-info {
      display: flex;
      align-items: center;
      gap: 1.25rem;
    }

    .timer-display {
      font-family: var(--font-mono);
      font-size: 2.3rem;
      font-weight: 700;
      color: var(--accent-cyan);
      min-width: 110px;
      text-shadow: 0 0 15px rgba(6, 182, 212, 0.4);
    }

    .timer-display.warning {
      color: var(--accent-amber);
      text-shadow: 0 0 15px rgba(245, 158, 11, 0.4);
    }

    .timer-display.danger {
      color: var(--accent-rose);
      text-shadow: 0 0 15px rgba(244, 63, 94, 0.5);
      animation: pulse 1s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    .timer-label h4 {
      font-family: var(--font-display);
      font-size: 0.95rem;
      color: var(--text-primary);
      margin-bottom: 0.15rem;
    }

    .timer-label p {
      font-size: 0.78rem;
      color: var(--text-muted);
      margin: 0;
      line-height: 1.35;
    }

    .timer-controls {
      display: flex;
      gap: 0.5rem;
    }

    .btn {
      font-family: var(--font-body);
      font-weight: 600;
      font-size: 0.82rem;
      padding: 0.55rem 1rem;
      border-radius: var(--radius-sm);
      border: none;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      transition: all 0.2s ease;
      touch-action: manipulation;
    }

    .btn:active {
      transform: scale(0.97);
    }

    .btn-primary {
      background: linear-gradient(135deg, #0284C7, #2563EB);
      color: #fff;
      box-shadow: 0 2px 10px rgba(2, 132, 199, 0.3);
    }

    .btn-primary:hover {
      background: linear-gradient(135deg, #0369A1, #1D4ED8);
    }

    .btn-secondary {
      background: var(--bg-surface-elevated);
      color: var(--text-primary);
      border: 1px solid var(--border-subtle);
    }

    .btn-secondary:hover {
      background: #1E293B;
      border-color: #334155;
    }

    .timer-bar-wrap {
      width: 100%;
      height: 6px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 999px;
      overflow: hidden;
      margin-top: 0.25rem;
    }

    .timer-bar-fill {
      height: 100%;
      width: 100%;
      background: linear-gradient(90deg, #10B981, #06B6D4);
      transition: width 0.2s linear, background 0.3s ease;
    }

    /* 5 Windows Pre-Check Grid */
    .windows-section {
      margin-bottom: 2rem;
    }

    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.85rem;
      border-bottom: 1px solid var(--border-subtle);
      padding-bottom: 0.65rem;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .section-header h2 {
      font-family: var(--font-display);
      font-size: 1.25rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .windows-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 0.75rem;
    }

    .window-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 0.85rem 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
      transition: all 0.2s ease;
      cursor: pointer;
      user-select: none;
      touch-action: manipulation;
    }

    .window-card:active {
      transform: scale(0.98);
    }

    .window-card.checked {
      border-color: var(--accent-emerald);
      background: rgba(16, 185, 129, 0.06);
    }

    .window-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .window-num {
      font-family: var(--font-display);
      font-weight: 700;
      font-size: 0.75rem;
      color: var(--accent-cyan);
    }

    .check-circle {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      border: 2px solid var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
      transition: all 0.2s;
    }

    .window-card.checked .check-circle {
      background: var(--accent-emerald);
      border-color: var(--accent-emerald);
      color: #fff;
    }

    .window-card h4 {
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--text-primary);
    }

    .window-card p {
      font-size: 0.75rem;
      color: var(--text-muted);
      line-height: 1.35;
    }

    /* Search & Swipeable Filter Toolbar */
    .toolbar {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 0.85rem 1rem;
      margin-bottom: 1.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .search-box {
      position: relative;
      width: 100%;
    }

    .search-input {
      width: 100%;
      background: var(--bg-main);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 0.7rem 1rem 0.7rem 2.4rem;
      color: var(--text-primary);
      font-size: 0.9rem;
      font-family: var(--font-body);
      outline: none;
      transition: all 0.2s;
      min-height: 44px;
    }

    .search-input:focus {
      border-color: var(--accent-blue);
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15);
    }

    .search-icon {
      position: absolute;
      left: 0.85rem;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      font-size: 0.9rem;
    }

    /* Swipeable filter pills (app-like horizontal flick on mobile) */
    .filter-pills {
      display: flex;
      flex-wrap: nowrap;
      overflow-x: auto;
      gap: 0.5rem;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: none;
      padding: 0.2rem 0;
    }

    .filter-pills::-webkit-scrollbar {
      display: none;
    }

    .filter-btn {
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      padding: 0.4rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.78rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
      flex-shrink: 0;
      touch-action: manipulation;
    }

    .filter-btn:active {
      transform: scale(0.95);
    }

    .filter-btn.active {
      background: var(--accent-blue);
      color: #0F172A;
      border-color: var(--accent-blue);
      font-weight: 700;
    }

    /* Questions List */
    .questions-list {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
      margin-bottom: 2.5rem;
    }

    .q-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-xl);
      padding: 1.5rem;
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      box-shadow: var(--shadow-card);
      transition: all 0.25s ease;
      position: relative;
    }

    .q-card:hover {
      border-color: rgba(56, 189, 248, 0.35);
    }

    .q-card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 0.85rem;
      gap: 0.75rem;
      flex-wrap: wrap;
    }

    .q-card-badges {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.4rem;
    }

    .q-id-badge {
      background: var(--accent-indigo);
      color: #fff;
      font-family: var(--font-display);
      font-weight: 800;
      font-size: 0.75rem;
      padding: 0.15rem 0.5rem;
      border-radius: var(--radius-sm);
    }

    .q-title {
      font-family: var(--font-display);
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--text-primary);
      margin-top: 0.4rem;
      line-height: 1.35;
    }

    /* Official Question Box */
    .question-box {
      background: rgba(14, 165, 233, 0.08);
      border-left: 4px solid var(--accent-blue);
      border-radius: 0 var(--radius-md) var(--radius-md) 0;
      padding: 0.85rem 1rem;
      margin-bottom: 0.85rem;
    }

    .question-box-label {
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--accent-blue);
      margin-bottom: 0.25rem;
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }

    .question-box-text {
      font-size: 0.98rem;
      font-style: italic;
      color: #E2E8F0;
      line-height: 1.45;
    }

    /* Alarm Warning Box */
    .alarm-box {
      background: rgba(244, 63, 94, 0.08);
      border-left: 4px solid var(--accent-rose);
      border-radius: 0 var(--radius-md) var(--radius-md) 0;
      padding: 0.75rem 1rem;
      margin-bottom: 1rem;
    }

    .alarm-label {
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--accent-rose);
      margin-bottom: 0.2rem;
      display: flex;
      align-items: center;
      gap: 0.3rem;
    }

    .alarm-text {
      font-size: 0.84rem;
      color: #FDA4AF;
      line-height: 1.4;
    }

    /* 4 Steps Container */
    .steps-container {
      background: rgba(15, 23, 42, 0.7);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 1rem;
      margin-bottom: 1rem;
    }

    .steps-label {
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--accent-emerald);
      margin-bottom: 0.65rem;
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }

    .steps-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 0.65rem;
    }

    .step-item {
      background: var(--bg-surface);
      border-radius: var(--radius-sm);
      padding: 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      border-left: 3px solid rgba(255, 255, 255, 0.1);
    }

    .step-item.step-1 { border-left-color: var(--accent-cyan); }
    .step-item.step-2 { border-left-color: var(--accent-blue); }
    .step-item.step-3 { border-left-color: var(--accent-rose); }
    .step-item.step-4 { border-left-color: var(--accent-emerald); }

    .step-header {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--accent-cyan);
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }

    .step-content {
      font-size: 0.82rem;
      color: var(--text-secondary);
      line-height: 1.4;
    }

    /* Code Snippet Box */
    .code-box {
      background: #090D14;
      border: 1px solid #1E293B;
      border-radius: var(--radius-md);
      margin-bottom: 0.85rem;
      overflow: hidden;
    }

    .code-box-header {
      background: #111827;
      padding: 0.45rem 0.85rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #1E293B;
      gap: 0.5rem;
    }

    .code-box-title {
      font-family: var(--font-mono);
      font-size: 0.72rem;
      color: #8B949E;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .copy-btn {
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #C9D1D9;
      font-size: 0.72rem;
      font-family: var(--font-body);
      padding: 0.3rem 0.65rem;
      border-radius: 4px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.3rem;
      transition: all 0.2s;
      flex-shrink: 0;
      touch-action: manipulation;
      min-height: 32px;
    }

    .copy-btn:active {
      transform: scale(0.95);
    }

    .copy-btn.copied {
      background: var(--accent-emerald);
      color: #fff;
      border-color: var(--accent-emerald);
    }

    pre.code-content {
      padding: 0.85rem;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: #E6EDF3;
      overflow-x: auto;
      line-height: 1.45;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: thin;
      scrollbar-color: #334155 transparent;
    }

    /* Terminal Command Box (Essential live tests) */
    .terminal-box {
      background: #060910;
      border: 1px solid rgba(245, 158, 11, 0.35);
      border-radius: var(--radius-md);
      overflow: hidden;
      box-shadow: 0 4px 15px rgba(245, 158, 11, 0.06);
    }

    .terminal-header {
      background: #111726;
      padding: 0.45rem 0.85rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(245, 158, 11, 0.2);
      gap: 0.5rem;
    }

    .terminal-dots {
      display: flex;
      gap: 5px;
    }

    .dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
    }
    .dot-red { background: #EF4444; }
    .dot-yellow { background: #F59E0B; }
    .dot-green { background: #10B981; }

    .terminal-title {
      font-family: var(--font-mono);
      font-size: 0.7rem;
      color: #FCD34D;
      font-weight: 600;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .terminal-body {
      padding: 0.85rem;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: #FDE68A;
      overflow-x: auto;
      line-height: 1.45;
      white-space: pre-wrap;
      word-break: break-all;
      -webkit-overflow-scrolling: touch;
    }

    .prompt-sym {
      color: #10B981;
      font-weight: 700;
      user-select: none;
    }

    /* Extra Sections: Modificación Señalada & Bitácora */
    .card-full {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-xl);
      padding: 1.75rem;
      margin-bottom: 1.75rem;
    }

    .card-full h3 {
      font-family: var(--font-display);
      font-size: 1.25rem;
      margin-bottom: 0.75rem;
      color: var(--text-primary);
    }

    .scenarios-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 0.85rem;
      margin-top: 0.85rem;
    }

    .scenario-card {
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 1.15rem;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }

    .scenario-card h4 {
      font-size: 0.9rem;
      color: var(--accent-cyan);
    }

    .scenario-card p {
      font-size: 0.78rem;
      color: var(--text-secondary);
      line-height: 1.4;
    }

    .errors-list {
      display: flex;
      flex-direction: column;
      gap: 0.65rem;
      margin-top: 0.85rem;
    }

    .error-item {
      background: var(--bg-surface-elevated);
      border-left: 3px solid var(--accent-amber);
      padding: 0.75rem 1rem;
      border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
      font-size: 0.8rem;
      color: var(--text-secondary);
      line-height: 1.4;
    }

    .error-item strong {
      color: var(--text-primary);
    }

    /* Toast Notification */
    .toast {
      position: fixed;
      bottom: max(1.5rem, env(safe-area-inset-bottom));
      left: 50%;
      transform: translateX(-50%) translateY(100px);
      background: var(--accent-emerald);
      color: #fff;
      font-family: var(--font-body);
      font-weight: 600;
      font-size: 0.82rem;
      padding: 0.65rem 1.25rem;
      border-radius: 9999px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      display: flex;
      align-items: center;
      gap: 0.5rem;
      opacity: 0;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      z-index: 1000;
      white-space: nowrap;
    }

    .toast.show {
      transform: translateX(-50%) translateY(0);
      opacity: 1;
    }

    /* Back to Top FAB button */
    .btn-fab {
      position: fixed;
      bottom: max(1.5rem, env(safe-area-inset-bottom));
      right: 1.25rem;
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: rgba(30, 41, 59, 0.9);
      border: 1px solid var(--border-subtle);
      color: var(--accent-blue);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.2rem;
      box-shadow: 0 6px 20px rgba(0,0,0,0.5);
      z-index: 90;
      cursor: pointer;
      opacity: 0;
      transform: scale(0.8);
      transition: all 0.25s ease;
      touch-action: manipulation;
    }

    .btn-fab.visible {
      opacity: 1;
      transform: scale(1);
    }

    .btn-fab:active {
      transform: scale(0.92);
    }

    /* Footer */
    footer {
      border-top: 1px solid var(--border-subtle);
      padding: 2rem 1.5rem;
      padding-bottom: max(2rem, env(safe-area-inset-bottom));
      text-align: center;
      color: var(--text-muted);
      font-size: 0.8rem;
    }

    /* -------------------------------------------------------------
       MOBILE-FIRST RESPONSIVE BREAKPOINTS
       ------------------------------------------------------------- */
    @media (max-width: 640px) {
      .top-bar {
        padding: 0.5rem 0.85rem;
        padding-top: max(0.5rem, env(safe-area-inset-top));
      }

      .brand-title {
        font-size: 0.92rem;
      }

      .nav-stats {
        gap: 0.3rem;
      }

      .stat-chip {
        padding: 0.2rem 0.45rem;
        font-size: 0.7rem;
      }

      .stat-chip span.label {
        display: none; /* Hide 'Preguntas', 'Tests' label on mobile to save space */
      }

      .container {
        padding: 0.85rem;
      }

      .hero {
        padding: 1.25rem 1rem;
        border-radius: var(--radius-lg);
        margin-bottom: 1.25rem;
      }

      .hero h1 {
        font-size: 1.55rem;
        line-height: 1.25;
      }

      .hero p {
        font-size: 0.88rem;
        margin-bottom: 1.15rem;
      }

      .timer-widget {
        flex-direction: column;
        align-items: stretch;
        padding: 1rem;
        gap: 1rem;
      }

      .timer-info {
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 0.5rem;
      }

      .timer-display {
        font-size: 2.5rem;
        min-width: auto;
      }

      .timer-controls {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        width: 100%;
        gap: 0.4rem;
      }

      .timer-controls .btn {
        padding: 0.65rem 0.3rem;
        font-size: 0.75rem;
        min-height: 42px;
      }

      .windows-grid {
        grid-template-columns: 1fr;
      }

      .windows-section {
        margin-bottom: 1.5rem;
      }

      .toolbar {
        padding: 0.75rem;
        border-radius: var(--radius-md);
        margin-bottom: 1.25rem;
      }

      .q-card {
        padding: 1rem;
        border-radius: var(--radius-lg);
      }

      .q-title {
        font-size: 1.05rem;
      }

      .question-box {
        padding: 0.75rem 0.85rem;
      }

      .question-box-text {
        font-size: 0.9rem;
      }

      .steps-grid {
        grid-template-columns: 1fr;
      }

      .scenarios-grid {
        grid-template-columns: 1fr;
      }

      .card-full {
        padding: 1.25rem 1rem;
        border-radius: var(--radius-lg);
      }

      .sticky-mini-timer {
        top: auto;
        bottom: max(1.5rem, env(safe-area-inset-bottom));
        right: auto;
        left: 1rem;
        padding: 0.4rem 0.9rem;
        font-size: 0.8rem;
      }
    }
  </style>
</head>
<body>

  <!-- Top Sticky Bar -->
  <header class="top-bar">
    <div class="brand-group">
      <span class="brand-badge">EP1 · D6</span>
      <span class="brand-title">Simulador de Defensa</span>
    </div>
    <div class="nav-stats">
      <div class="stat-chip"><strong>17</strong><span class="label"> Preguntas</span></div>
      <div class="stat-chip"><strong>7</strong><span class="label"> Tests</span></div>
      <div class="stat-chip"><strong>4</strong><span class="label"> Pasos</span></div>
    </div>
  </header>

  <!-- Sticky Mini-Timer Pill (Appears on scroll) -->
  <div class="sticky-mini-timer" id="stickyMiniTimer" onclick="scrollToTimer()">
    <span id="miniTimerIcon">⏱️</span>
    <span id="miniTimerDisplay">01:00</span>
  </div>

  <main class="container">

    <!-- Hero & 60s Drill Timer -->
    <section class="hero" id="heroSection">
      <div class="hero-meta">
        <span class="tag tag-blue">DSY1107 · Cloud Native I</span>
        <span class="tag tag-green">Caso VidalStore</span>
        <span class="tag tag-purple">Ponderación: 60% Oral</span>
        <span class="tag tag-rose">Regla del Reloj (60s)</span>
      </div>
      <h1>Guía Maestra y Simulador de Defensa Técnica</h1>
      <p>
        El docente <strong>Cristian Calderón</strong> evalúa la autoría técnica y el dominio de punta a punta. 
        Si te vas por las ramas, te corta a los 60 segundos. Abre el archivo en el editor, explica con el 
        framework de 4 pasos (Qué hice, Qué resuelve, Qué descarté, Cómo lo compruebo) y ejecuta los tests esenciales en la terminal.
      </p>

      <!-- 60-Second Stopwatch Drill -->
      <div class="timer-widget" id="mainTimerWidget">
        <div class="timer-info">
          <div class="timer-display" id="timerDisplay">01:00</div>
          <div class="timer-label">
            <h4>Simulador del Reloj de 60 Segundos</h4>
            <p id="timerFeedback">Entrena tu respuesta: directo al código y al grano antes de que suene el corte.</p>
          </div>
        </div>
        <div class="timer-controls">
          <button class="btn btn-primary" id="btnTimerStart" onclick="startTimer()">▶ Iniciar</button>
          <button class="btn btn-secondary" id="btnTimerPause" onclick="pauseTimer()">⏸ Pausa</button>
          <button class="btn btn-secondary" id="btnTimerReset" onclick="resetTimer()">🔄 Reset</button>
        </div>
        <div class="timer-bar-wrap">
          <div class="timer-bar-fill" id="timerBar"></div>
        </div>
      </div>
    </section>

    <!-- 5 Windows Checklist -->
    <section class="windows-section">
      <div class="section-header">
        <h2>🖥️ Tablero de Control: 5 Ventanas Obligatorias</h2>
        <span class="stat-chip" id="windowsCounter">0 de 5 listas</span>
      </div>
      <div class="windows-grid">
        <div class="window-card" onclick="toggleWindow(this)">
          <div class="window-top">
            <span class="window-num">VENTANA 1</span>
            <span class="check-circle">✓</span>
          </div>
          <h4>Terminal con Procesos</h4>
          <p>Angular (4200), Gateway (8080), BFF (3001), Catálogo (3002), Biblioteca (3003), Compras (3004), Logs (3005).</p>
        </div>

        <div class="window-card" onclick="toggleWindow(this)">
          <div class="window-top">
            <span class="window-num">VENTANA 2</span>
            <span class="check-circle">✓</span>
          </div>
          <h4>Navegador (Angular)</h4>
          <p>http://localhost:4200 con sesión abierta, pestaña Red limpia en Fetch/XHR apuntando solo a 8080.</p>
        </div>

        <div class="window-card" onclick="toggleWindow(this)">
          <div class="window-top">
            <span class="window-num">VENTANA 3</span>
            <span class="check-circle">✓</span>
          </div>
          <h4>Terminal / Tokens curl</h4>
          <p>Variables $TOKEN_JUGADOR y $TOKEN_ADMIN cargadas y listas para probar 403 vs 200 al instante.</p>
        </div>

        <div class="window-card" onclick="toggleWindow(this)">
          <div class="window-top">
            <span class="window-num">VENTANA 4</span>
            <span class="check-circle">✓</span>
          </div>
          <h4>Editor VS Code</h4>
          <p>token.interceptor.ts, gateway.controller.ts, bff-biblioteca.controller.ts, seed.ts, biblioteca.service.ts.</p>
        </div>

        <div class="window-card" onclick="toggleWindow(this)">
          <div class="window-top">
            <span class="window-num">VENTANA 5</span>
            <span class="check-circle">✓</span>
          </div>
          <h4>AWS Cognito Console</h4>
          <p>User Pool abierto mostrando usuarios, grupos (jugadores, administradores) y los 2 App Clients.</p>
        </div>
      </div>
    </section>

    <!-- Search & Swipeable Filter Toolbar -->
    <section class="toolbar">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input 
          type="text" 
          id="searchInput" 
          class="search-input" 
          placeholder="Buscar pregunta, concepto (sub, UUID, 409), código..."
          oninput="filterQuestions()"
        />
      </div>
      <div class="filter-pills" id="filterPills">
        <button class="filter-btn active" onclick="setFilter('all', this)">Todas (17)</button>
        <button class="filter-btn" onclick="setFilter('Flujo A', this)">Flujo A · Identidad</button>
        <button class="filter-btn" onclick="setFilter('Flujo B', this)">Flujo B · Red & BFF</button>
        <button class="filter-btn" onclick="setFilter('Flujo C', this)">Flujo C · Roles</button>
        <button class="filter-btn" onclick="setFilter('Flujo D', this)">Flujo D · Zero Trust</button>
        <button class="filter-btn" onclick="setFilter('Flujo E', this)">Flujo E · Catálogo</button>
        <button class="filter-btn" onclick="setFilter('Reglas de Negocio', this)">Reglas, Licencias e IDs (6)</button>
        <button class="filter-btn" onclick="setFilter('tests-only', this)">⚡ Solo Pruebas en Vivo (7)</button>
      </div>
    </section>

    <!-- Questions Container -->
    <section class="questions-list" id="questionsContainer">
      <!-- Injected by JavaScript -->
    </section>

    <!-- La Modificación Señalada Simulator -->
    <section class="card-full">
      <div class="section-header">
        <h2>🛠️ Minutos 12 a 14: La Modificación Señalada</h2>
      </div>
      <p style="color: var(--text-secondary); margin-bottom: 0.85rem; font-size: 0.88rem;">
        El docente pide una modificación sobre un frente que <strong>no programaste tú</strong>. 
        <strong>No se programa en vivo:</strong> se abre el archivo en el editor, se apunta la línea y se explica qué se escribiría:
      </p>
      <div class="scenarios-grid">
        <div class="scenario-card">
          <h4>1. Ruta Solo para Administradores</h4>
          <p><strong>Archivo:</strong> <code>bff-licencias.controller.ts</code> y <code>gateway.controller.ts</code></p>
          <p><strong>Acción:</strong> Agregar <code>@RequireGroups('administradores')</code> y <code>@UseGuards(AuthGuard, GroupsGuard)</code>.</p>
          <p><strong>Comprobación:</strong> Con jugador responde <code>403 Forbidden</code>; con admin responde <code>200 OK</code>.</p>
        </div>

        <div class="scenario-card">
          <h4>2. Comentar Cabecera en Interceptor</h4>
          <p><strong>Archivo:</strong> <code>src/app/auth/token.interceptor.ts</code></p>
          <p><strong>Acción:</strong> Comentar <code>setHeaders: { Authorization: ... }</code>.</p>
          <p><strong>Comprobación:</strong> Peticiones salen limpias: el Gateway corta inmediatamente con <code>401 Unauthorized</code>.</p>
        </div>

        <div class="scenario-card">
          <h4>3. Configurar Client ID Equivocado</h4>
          <p><strong>Archivo:</strong> <code>vidalstore-gateway/.env</code></p>
          <p><strong>Acción:</strong> Cambiar <code>COGNITO_CLIENT_ID</code> por el del App Client 2 (backend con secret).</p>
          <p><strong>Comprobación:</strong> Firma RSA pasa, pero <code>auth.service.ts</code> falla en <code>client_id !== expected</code> arrojando <code>401</code>.</p>
        </div>

        <div class="scenario-card">
          <h4>4. Quitar Microservicio del Promise.all</h4>
          <p><strong>Archivo:</strong> <code>bff-biblioteca.controller.ts</code></p>
          <p><strong>Acción:</strong> Quitar llamada al microservicio de Catálogo dentro de <code>Promise.all</code>.</p>
          <p><strong>Comprobación:</strong> El endpoint responde licencias pero con <code>juego: null</code>; la UI queda sin títulos ni portadas.</p>
        </div>
      </div>
    </section>

    <!-- Bitácora de Errores Reales -->
    <section class="card-full">
      <div class="section-header">
        <h2>📖 Bitácora de Errores Reales del Proyecto (D6 "Qué Descarté")</h2>
      </div>
      <p style="color: var(--text-secondary); font-size: 0.88rem;">
        Mencionar un error real que cometiste y cómo lo resolviste demuestra autoría genuina mucho más que una respuesta de memoria:
      </p>
      <div class="errors-list">
        <div class="error-item">
          <strong>1. App Client con secreto en Angular:</strong> Creamos un client con secret key; Amplify en el browser no lo soportaba. <em>Solución:</em> Creamos App Client 1 público sin secret.
        </div>
        <div class="error-item">
          <strong>2. Token expirado en pruebas de curl:</strong> Llamadas daban 401 repentino. <em>Solución:</em> El token de Cognito vence a los 60 min (claim <code>exp</code>); automatizamos la renovación.
        </div>
        <div class="error-item">
          <strong>3. Trampa de Cognito en auto-registro:</strong> Al registrarse por Hosted UI, <code>cognito:groups</code> venía vacío dando 403. <em>Solución:</em> Fallback seguro a <code>['jugadores']</code> en <code>groups.guard.ts</code>.
        </div>
        <div class="error-item">
          <strong>4. CORS configurado en el BFF:</strong> Intentamos poner CORS en el puerto 3001. <em>Solución:</em> CORS solo aplica en navegador contra el Gateway (8080); entre Node.js no aplica.
        </div>
        <div class="error-item">
          <strong>5. Interceptor enviando JWT a Google Fonts:</strong> El interceptor inyectaba Bearer a fuentes externas. <em>Solución:</em> Whitelist estricta <code>PERMITIDOS = ['http://localhost:8080']</code>.
        </div>
      </div>
    </section>

  </main>

  <!-- Back to top FAB button -->
  <button class="btn-fab" id="btnBackToTop" onclick="scrollToTop()" title="Volver arriba">↑</button>

  <!-- Copy Toast Notification -->
  <div class="toast" id="toast">✓ Copiado al portapapeles</div>

  <footer>
    <p>VidalStore EP1 · DSY1107 Desarrollo Cloud Native I · DUOC UC (2026-02)</p>
    <p style="margin-top: 0.25rem;">Basado en la Clase Magistral D6 y Resoluciones del Profesor Cristian Calderón</p>
  </footer>

  <!-- Embedded Data & Interactive Engine -->
  <script>
    const DIALOGUES = __DIALOGUES_DATA__;

    let currentFilter = 'all';
    let searchQuery = '';

    // Render questions
    function renderQuestions() {
      const container = document.getElementById('questionsContainer');
      container.innerHTML = '';

      const filtered = DIALOGUES.filter(item => {
        const matchesCategory = 
          currentFilter === 'all' ? true :
          currentFilter === 'tests-only' ? (item.cmd && item.cmd.trim() !== '') :
          item.section.toLowerCase().includes(currentFilter.toLowerCase());

        const query = searchQuery.toLowerCase().trim();
        const matchesSearch = query === '' ? true : (
          item.id.toLowerCase().includes(query) ||
          item.title.toLowerCase().includes(query) ||
          item.question.toLowerCase().includes(query) ||
          (item.alarm && item.alarm.toLowerCase().includes(query)) ||
          item.steps.some(s => s[1].toLowerCase().includes(query) || s[2].toLowerCase().includes(query)) ||
          (item.code && item.code.toLowerCase().includes(query)) ||
          (item.cmd && item.cmd.toLowerCase().includes(query))
        );

        return matchesCategory && matchesSearch;
      });

      if (filtered.length === 0) {
        container.innerHTML = `
          <div style="text-align: center; padding: 3rem 1.5rem; color: var(--text-muted); background: var(--bg-surface); border-radius: var(--radius-xl); border: 1px dashed var(--border-subtle);">
            <h3 style="font-size: 1.1rem;">No se encontraron preguntas</h3>
            <p style="margin-top: 0.4rem; font-size: 0.85rem;">Prueba con "sub", "Cognito", "BFF", "409", "CORS" o limpia los filtros.</p>
          </div>
        `;
        return;
      }

      filtered.forEach(item => {
        const card = document.createElement('article');
        card.className = 'q-card';
        card.id = `q-${item.id}`;

        let stepsHtml = '';
        item.steps.forEach(([num, title, content]) => {
          const icon = num === '1' ? '🛠️' : num === '2' ? '💡' : num === '3' ? '🚫' : '🧪';
          stepsHtml += `
            <div class="step-item step-${num}">
              <span class="step-header">${icon} ${num}. ${title}</span>
              <p class="step-content">${escapeHtml(content)}</p>
            </div>
          `;
        });

        let codeBlock = '';
        if (item.code) {
          codeBlock = `
            <div class="code-box">
              <div class="code-box-header">
                <span class="code-box-title">Extracto de Código</span>
                <button class="copy-btn" onclick="copyCode('${item.id}', this)">
                  📋 Copiar
                </button>
              </div>
              <pre class="code-content"><code>${escapeHtml(item.code)}</code></pre>
            </div>
          `;
        }

        let cmdBlock = '';
        if (item.cmd) {
          cmdBlock = `
            <div class="terminal-box">
              <div class="terminal-header">
                <div class="terminal-dots">
                  <span class="dot dot-red"></span>
                  <span class="dot dot-yellow"></span>
                  <span class="dot dot-green"></span>
                </div>
                <span class="terminal-title">Test en Vivo (Terminal)</span>
                <button class="copy-btn" onclick="copyCmd('${item.id}', this)">
                  ⚡ Copiar
                </button>
              </div>
              <div class="terminal-body"><span class="prompt-sym">$ </span>${escapeHtml(item.cmd)}</div>
            </div>
          `;
        }

        card.innerHTML = `
          <div class="q-card-header">
            <div>
              <div class="q-card-badges">
                <span class="q-id-badge">${item.id}</span>
                <span class="tag tag-blue">${item.section}</span>
                ${item.cmd ? '<span class="tag tag-green">⚡ Test en Vivo</span>' : ''}
              </div>
              <h3 class="q-title">${item.title}</h3>
            </div>
          </div>

          <div class="question-box">
            <div class="question-box-label">
              <span>👤</span> Pregunta Oficial de Cristian Calderón:
            </div>
            <p class="question-box-text">«${item.question}»</p>
          </div>

          ${item.alarm ? `
            <div class="alarm-box">
              <div class="alarm-label">
                <span>⚠️</span> SEÑAL DE ALARMA DE D6 (Lo que NUNCA debes decir):
              </div>
              <p class="alarm-text">${item.alarm}</p>
            </div>
          ` : ''}

          <div class="steps-container">
            <div class="steps-label">
              <span>🎯</span> Framework de Respuesta en 4 Pasos (D6)
            </div>
            <div class="steps-grid">
              ${stepsHtml}
            </div>
          </div>

          ${codeBlock}
          ${cmdBlock}
        `;

        container.appendChild(card);
      });
    }

    function escapeHtml(text) {
      return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }

    function copyCode(id, btn) {
      const item = DIALOGUES.find(d => d.id === id);
      if (item && item.code) {
        copySnippet(btn, item.code);
      }
    }

    function copyCmd(id, btn) {
      const item = DIALOGUES.find(d => d.id === id);
      if (item && item.cmd) {
        copySnippet(btn, item.cmd);
      }
    }

    // Filter by category
    function setFilter(cat, btn) {
      currentFilter = cat;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      renderQuestions();
    }

    // Realtime search
    function filterQuestions() {
      searchQuery = document.getElementById('searchInput').value;
      renderQuestions();
    }

    // 5 Windows Pre-flight checklist
    function toggleWindow(card) {
      card.classList.toggle('checked');
      updateWindowsCounter();
    }

    function updateWindowsCounter() {
      const checked = document.querySelectorAll('.window-card.checked').length;
      const counter = document.getElementById('windowsCounter');
      counter.textContent = `${checked} de 5 listas (${checked * 20}%)`;
      if (checked === 5) {
        counter.style.color = 'var(--accent-emerald)';
        counter.textContent = "✓ 5 de 5 listas · 100% Preparado";
      } else {
        counter.style.color = 'var(--accent-blue)';
      }
    }

    // Copy to clipboard
    function copySnippet(btn, text) {
      navigator.clipboard.writeText(text).then(() => {
        const origText = btn.innerHTML;
        btn.innerHTML = '✓ Copiado';
        btn.classList.add('copied');
        showToast();
        setTimeout(() => {
          btn.innerHTML = origText;
          btn.classList.remove('copied');
        }, 1800);
      });
    }

    function showToast() {
      const toast = document.getElementById('toast');
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2000);
    }

    // Scroll helpers
    function scrollToTop() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function scrollToTimer() {
      const hero = document.getElementById('heroSection');
      if (hero) hero.scrollIntoView({ behavior: 'smooth' });
    }

    // 60-Second Timer Engine
    let timerDuration = 60;
    let timerRemaining = 60;
    let timerInterval = null;
    let isRunning = false;

    function formatTime(secs) {
      const m = Math.floor(secs / 60).toString().padStart(2, '0');
      const s = (secs % 60).toString().padStart(2, '0');
      return `${m}:${s}`;
    }

    function updateTimerUI() {
      const display = document.getElementById('timerDisplay');
      const miniDisplay = document.getElementById('miniTimerDisplay');
      const miniPill = document.getElementById('stickyMiniTimer');
      const bar = document.getElementById('timerBar');
      const feedback = document.getElementById('timerFeedback');

      const formatted = formatTime(timerRemaining);
      display.textContent = formatted;
      if (miniDisplay) miniDisplay.textContent = formatted;

      const pct = (timerRemaining / timerDuration) * 100;
      bar.style.width = `${pct}%`;

      display.className = 'timer-display';
      if (miniPill) miniPill.classList.remove('danger');

      if (timerRemaining <= 10) {
        display.classList.add('danger');
        if (miniPill) miniPill.classList.add('danger');
        bar.style.background = 'linear-gradient(90deg, #F43F5E, #E11D48)';
        feedback.textContent = "🚨 ¡ÚLTIMOS 10s! Concreción: Cierra con el Paso 4.";
      } else if (timerRemaining <= 25) {
        display.classList.add('warning');
        bar.style.background = 'linear-gradient(90deg, #F59E0B, #D97706)';
        feedback.textContent = "⚠️ 25s restantes: Pasa al Paso 3 (Qué descarté).";
      } else {
        bar.style.background = 'linear-gradient(90deg, #10B981, #06B6D4)';
        feedback.textContent = "⏱️ Respondiendo: Abre el archivo en el editor y sigue los 4 pasos.";
      }
    }

    function startTimer() {
      if (isRunning) return;
      isRunning = true;
      document.getElementById('btnTimerStart').textContent = "▶ Corriendo";

      timerInterval = setInterval(() => {
        if (timerRemaining > 0) {
          timerRemaining--;
          updateTimerUI();
        } else {
          clearInterval(timerInterval);
          isRunning = false;
          document.getElementById('btnTimerStart').textContent = "▶ Iniciar";
          playChime();
        }
      }, 1000);
    }

    function pauseTimer() {
      clearInterval(timerInterval);
      isRunning = false;
      document.getElementById('btnTimerStart').textContent = "▶ Seguir";
    }

    function resetTimer() {
      clearInterval(timerInterval);
      isRunning = false;
      timerRemaining = timerDuration;
      document.getElementById('btnTimerStart').textContent = "▶ Iniciar";
      updateTimerUI();
      document.getElementById('timerFeedback').textContent = "Entrena tu respuesta: directo al código y al grano antes de que suene el corte.";
    }

    function playChime() {
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.3);
        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.8);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.8);
      } catch (e) {}
    }

    // Scroll listener for sticky mini-timer and Back to top FAB
    window.addEventListener('scroll', () => {
      const scrollY = window.scrollY;
      const hero = document.getElementById('heroSection');
      const miniTimer = document.getElementById('stickyMiniTimer');
      const btnFab = document.getElementById('btnBackToTop');

      const heroBottom = hero ? (hero.offsetTop + hero.offsetHeight) : 350;

      if (scrollY > heroBottom - 50) {
        if (miniTimer) miniTimer.classList.add('visible');
      } else {
        if (miniTimer) miniTimer.classList.remove('visible');
      }

      if (scrollY > 400) {
        if (btnFab) btnFab.classList.add('visible');
      } else {
        if (btnFab) btnFab.classList.remove('visible');
      }
    });

    window.addEventListener('DOMContentLoaded', () => {
      renderQuestions();
      updateWindowsCounter();
      updateTimerUI();
    });
  </script>
</body>
</html>
"""

def generate_html():
    content = TEMPLATE.replace("__DIALOGUES_DATA__", json.dumps(DIALOGUES))
    for path in [HTML_PATH_D6, HTML_PATH_MAIN]:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Interactive Mobile-Optimized HTML saved at: {path} ({os.path.getsize(path) / 1024:.1f} KB)")

if __name__ == "__main__":
    generate_html()
