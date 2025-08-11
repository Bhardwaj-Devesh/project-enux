import { useState } from "react";
import { X, Mail, Github, Chrome, BookOpen, User } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface LoginPopupProps {
  isOpen: boolean;
  onClose: () => void;
}

export function LoginPopup({ isOpen, onClose }: LoginPopupProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);

  const { signUp, signIn, signInWithProvider, signInAsGuest } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    
    if (isSignUp) {
      if (!fullName.trim()) {
        // Show error for missing full name
        return;
      }
      const { error } = await signUp(email, password, fullName);
      if (!error) {
        onClose();
      }
    } else {
      const { error } = await signIn(email, password);
      if (!error) {
        onClose();
      }
    }
  };

  const handleSocialLogin = async (provider: 'google' | 'github' | 'email') => {
    if (provider === 'email') {
      setIsSignUp(false);
      return;
    }
    
    const { error } = await signInWithProvider(provider);
    if (!error) {
      onClose();
    }
  };

  const resetForm = () => {
    setEmail("");
    setPassword("");
    setFullName("");
  };

  const handleModeSwitch = (signUpMode: boolean) => {
    setIsSignUp(signUpMode);
    resetForm();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center justify-center mb-4">
            <BookOpen className="h-8 w-8 text-primary mr-2" />
            <span className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              Enux
            </span>
          </div>
          <DialogTitle className="text-center">
            Welcome to the future of business knowledge
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Social Sign In */}
          <div className="space-y-3">
            <Button
              variant="outline"
              size="lg"
              className="w-full"
              onClick={() => handleSocialLogin("google")}
            >
              <Chrome className="h-5 w-5 mr-2" />
              Continue with Google
            </Button>
            
            <Button
              variant="outline"
              size="lg"
              className="w-full"
              onClick={() => handleSocialLogin("github")}
            >
              <Github className="h-5 w-5 mr-2" />
              Continue with GitHub
            </Button>
            
            <Button
              variant="outline"
              size="lg"
              className="w-full"
              onClick={() => handleSocialLogin("email")}
            >
              <Mail className="h-5 w-5 mr-2" />
              Continue with Email
            </Button>
            
            <Button
              variant="outline"
              size="lg"
              className="w-full"
              onClick={() => {
                signInAsGuest();
                onClose();
              }}
            >
              <User className="h-5 w-5 mr-2" />
              Continue as Guest
            </Button>
          </div>

          {/* Separator */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <Separator className="w-full" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">
                or create account
              </span>
            </div>
          </div>

          {/* Sign Up Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignUp && (
              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name</Label>
                <Input
                  id="fullName"
                  type="text"
                  placeholder="Enter your full name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required={isSignUp}
                />
              </div>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder={isSignUp ? "Create a password" : "Enter your password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <Button type="submit" size="lg" className="w-full">
              {isSignUp ? "Create Account" : "Sign In"}
            </Button>
            
            {!isSignUp && (
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => handleModeSwitch(true)}
                  className="text-sm text-primary hover:underline"
                >
                  Don't have an account? Sign up
                </button>
              </div>
            )}
            
            {isSignUp && (
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => handleModeSwitch(false)}
                  className="text-sm text-primary hover:underline"
                >
                  Already have an account? Sign in
                </button>
              </div>
            )}
          </form>

          {/* Terms and Privacy */}
          <div className="text-xs text-center text-muted-foreground">
            By continuing, you agree to our{" "}
            <a href="/terms" target="_blank" className="underline hover:text-primary">
              Terms of Service
            </a>{" "}
            and{" "}
            <a href="/privacy" target="_blank" className="underline hover:text-primary">
              Privacy Policy
            </a>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}