import NextAuth, { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import CredentialsProvider from "next-auth/providers/credentials";
import bcrypt from "bcryptjs";
import connectDB from "@/lib/mongodb";
import CredentialsUser from "@/models/CredentialsUser";

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID ?? "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
    }),
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error("Email and password required");
        }

        try {
          await connectDB();

          const user = await CredentialsUser.findOne({
            email: credentials.email,
          });

          if (!user) {
            throw new Error("Invalid credentials");
          }

          const isPasswordValid = await bcrypt.compare(
            credentials.password,
            user.password,
          );

          if (!isPasswordValid) {
            throw new Error("Invalid credentials");
          }

          return {
            id: user._id.toString(),
            email: user.email,
          };
        } catch (error) {
          console.error("Auth error:", error);
          throw error;
        }
      },
    }),
  ],
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async jwt({ token, user, account, profile }) {
      if (user) {
        // For credentials provider
        token.id = user.id;
        token.email = user.email;
      }

      // For Google OAuth
      if (account?.provider === "google" && profile?.sub) {
        token.id = profile.sub as string; // Google's user ID

        console.log("\n\n\nToken ID / User ID:\t\t\t", token.id, "\n\n\n");
      }

      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.email = token.email as string;
      }
      return session;
    },
  },
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
