import '@/styles/globals.css';
import 'antd/dist/reset.css';
import { ConfigProvider, Layout } from 'antd';
import type { AppProps } from 'next/app';
import MainLayout from '../components/mainLayout';
import { AuthProvider } from '../context';
import { theme } from '@/styles/theme';

const { Content } = Layout;

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: theme.colors.accent,
          colorLink: theme.colors.inkMid,
          colorInfo: theme.colors.accent,
          colorSuccess: '#5C7A3B',
          colorWarning: '#C6A96B',
          colorError: '#A13D3D',
          borderRadius: theme.radius.md,
          fontFamily: theme.fonts.sans
        },
        components: {
          Button: {
            primaryColor: theme.colors.accentInk,
            colorPrimaryHover: theme.colors.accentBorder,
            colorPrimaryActive: theme.colors.accentBorder
          }
        }
      }}
    >
      <AuthProvider>
        <MainLayout>
          <Content><Component {...pageProps} /></Content>
        </MainLayout>
      </AuthProvider>
    </ConfigProvider>
  );
}
