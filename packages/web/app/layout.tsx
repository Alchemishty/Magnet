export const metadata = {
  title: 'Magnet',
  description: 'Agentic UA creative production platform',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
