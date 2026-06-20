import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
});

export const metadata = {
  title: "HimalayanHawala",
  description: "Remittance Intelligence · Nepal",
  icons: {},
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${inter.className} antialiased`}>
      <body>{children}</body>
    </html>
  );
}
