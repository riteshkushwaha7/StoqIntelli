import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "StoqIntelli",
  description: "Stock forecasts with selected timeframes, sentiment analysis, and confidence insights."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
        <footer className="app-footer">
          <p>
            Created by{" "}
            <a href="https://www.linkedin.com/in/riteshkushwaha7/" target="_blank" rel="noreferrer">
              Ritesh Kushwaha
            </a>
          </p>
          <p>
            Project:{" "}
            <a href="https://github.com/riteshkushwaha7/StoqIntelli" target="_blank" rel="noreferrer">
              StoqIntelli on GitHub
            </a>
          </p>
        </footer>
      </body>
    </html>
  );
}
