# OMEGA Frontend - Next.js Premium Interface

A high-performance, aesthetically pleasing React frontend built with Next.js and Tailwind CSS. OMEGA provides a "glassmorphism" premium experience for car buyers.

## ✨ Key Features

-   **Intelligent Chat Dashboard**: A state-of-the-art interactive interface with real-time UI updates (modals, cards, adaptive forms).
-   **Market Insights**: Dynamic data visualization using Recharts to show price evolution and demand scores.
-   **Multi-Agent Coordination**: Real-time feedback from the OMEGA Brain during the negotiation flow.
-   **Premium Styling**: Built with Framer Motion for smooth transitions and a modern "dark nebula" aesthetic.

## 🏗️ Architecture

-   **Services Layer**: Clean API interaction via `chatService`, `negotiationService`, and `marketService`.
-   **Hooks**: `useChat` custom hook manages the complex state orchestration and multi-round negotiation logic.
-   **Context**: `AuthContext` handles global user session and JWT persistence.

## 🚀 Getting Started

1.  **Install Dependencies**:
    ```bash
    npm install
    ```
2.  **Environment Configuration**: Ensure `.env.local` points to the Backend API.
3.  **Run Development Server**:
    ```bash
    npm run dev
    ```

## 🎨 Design System

-   **Glassmorphism**: Heavy use of backdrop-blur and semi-transparent borders.
-   **Rich Aesthetics**: Deep blue/purple nebula backgrounds with vibrant accents.
-   **Micro-animations**: Interactive elements that feel alive under the cursor.
