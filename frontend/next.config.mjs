/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Não bloquear o build de produção por avisos de lint (ex.: imports não usados).
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
