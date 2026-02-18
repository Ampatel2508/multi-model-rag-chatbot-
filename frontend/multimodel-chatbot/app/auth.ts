import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

export const { auth, signIn, signOut } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
      allowDangerousEmailAccountLinking: true,
    }),
  ],
  pages: {
    signIn: "/login",
    signOut: "/login",
  },
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
