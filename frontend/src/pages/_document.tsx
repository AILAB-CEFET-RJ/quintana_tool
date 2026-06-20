import StyledComponentsRegistry from '@/lib/registry'
import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html lang="en">
      <Head>
      <link rel="icon" href="/favicon.ico" sizes="any" />
      <link rel="icon" href="/quintana-icon.svg" type="image/svg+xml" />
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" />
      <link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;500;600&family=Source+Sans+3:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      </Head>
      <body>
        <StyledComponentsRegistry>
          <Main />
          <NextScript />
        </StyledComponentsRegistry>
      </body>
    </Html>
  )
}
