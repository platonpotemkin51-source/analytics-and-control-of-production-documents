import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider, Layout } from 'antd';
import Dashboard from './pages/Dashboard';
import { woodflowTheme } from './theme/theme';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider theme={woodflowTheme}>
      <Layout style={{ minHeight: '100vh', padding: 24 }}>
        <Dashboard />
      </Layout>
    </ConfigProvider>
  </React.StrictMode>
);
