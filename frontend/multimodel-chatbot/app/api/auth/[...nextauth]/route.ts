import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

const handler = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
      allowDangerousEmailAccountLinking: true,
      authorization: {
        params: {
          redirect_uri: process.env.NEXTAUTH_CALLBACK_URL || `${process.env.NEXTAUTH_URL}/api/auth/callback/google`,
        },
      },
    }),
  ],
  pages: {
    signIn: "/login",
    signOut: "/login",
  },
  session: {
    strategy: "jwt",
  },
  useSecureCookies: process.env.NODE_ENV === "production",
  callbacks: {
    async jwt({ token, user, account }: any) {
      if (account && user) {
        token.id = user.id;
        token.googleId = account.providerAccountId;
      }
      return token;
    },
    async session({ session, token }: any) {
      if (session.user) {
        (session.user as any).id = token.id;
      }
      return session;
    },
    async redirect({ url, baseUrl }: any) {
      // Allow relative URLs
      if (url.startsWith("/")) {
        return `${baseUrl}${url}`;
      }
      // Allow same origin URLs
      if (new URL(url).origin === baseUrl) {
        return url;
      }
      // Default redirect to chat page
      return `${baseUrl}/chat`;
    },
  },
  events: {
    async signIn({ user, account }: any) {
      if (account?.provider === "google" && user.email) {
        try {
          await fetch("http://localhost:8000/api/auth/google", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              email: user.email,
              name: user.name,
              googleId: user.id,
              image: user.image,
            }),
          });
        } catch (error) {
          console.error("Failed to sync user with backend:", error);
        }
      }
    },
  },
});

export async function GET(
  req: Request,
  { params }: { params: Promise<{ nextauth: string[] }> | { nextauth: string[] } }
) {
  return handler(req, { params });
}

export async function POST(
  req: Request,
  { params }: { params: Promise<{ nextauth: string[] }> | { nextauth: string[] } }
) {
  return handler(req, { params });
}
