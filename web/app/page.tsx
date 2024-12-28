import { Features } from "@/components/Features";
import { Hero } from "@/components/Hero";
import { HowItWorks } from "@/components/HowItWorks";
import { motion } from "framer-motion";

export default function Home() {
  return (
    <>
      <Hero />
      <Features />
      <HowItWorks />
    </>
  );
}
