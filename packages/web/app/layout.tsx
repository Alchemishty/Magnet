import './globals.css';

import { Providers } from '@/components/providers';
import { AppShell } from '@/components/app-shell';

export const metadata = {
  title: 'Magnet',
  description: 'Agentic UA creative production platform',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
