import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useToast } from '@/hooks/use-toast';
import { API_BASE_URL } from '@/lib/utils';

// Backend API types
interface User {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
}

interface AuthError {
  message: string;
  status?: number;
}

interface AuthResponse {
  error?: AuthError;
  user?: User;
}

interface SignUpRequest {
  email: string;
  password: string;
  full_name: string;
  confirm_password: string;
}

interface SignInRequest {
  email: string;
  password: string;
}

interface AuthContextType {
  user: User | null;
  isGuest: boolean;
  signUp: (email: string, password: string, fullName: string) => Promise<{ error: AuthError | null }>;
  signIn: (email: string, password: string) => Promise<{ error: AuthError | null }>;
  signOut: () => Promise<void>;
  signInWithProvider: (provider: 'google' | 'github') => Promise<{ error: AuthError | null }>;
  signInAsGuest: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isGuest, setIsGuest] = useState(false);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    // Check for existing session from sessionStorage
    const userData = sessionStorage.getItem('user_data');
    
    if (userData) {
      try {
        const user = JSON.parse(userData);
        setUser(user);
        setLoading(false);
      } catch (error) {
        // Clear invalid data
        sessionStorage.removeItem('user_data');
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, []);

  const signUp = async (email: string, password: string, fullName: string): Promise<{ error: AuthError | null }> => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
          confirm_password: password,
        } as SignUpRequest),
      });

      const data = await response.json();

      if (!response.ok) {
        const error: AuthError = {
          message: data.detail || data.message || 'Registration failed',
          status: response.status,
        };
        
        toast({
          title: "Sign up failed",
          description: error.message,
          variant: "destructive",
        });
        
        return { error };
      }

      // Store user data from response
      sessionStorage.setItem('user_data', JSON.stringify(data));
      setUser(data);

      toast({
        title: "Account created successfully",
        description: "Welcome to Enux!",
      });

      return { error: null };
    } catch (error) {
      const authError: AuthError = {
        message: error instanceof Error ? error.message : 'Network error occurred',
      };
      
      toast({
        title: "Sign up failed",
        description: authError.message,
        variant: "destructive",
      });
      
      return { error: authError };
    }
  };

  const signIn = async (email: string, password: string): Promise<{ error: AuthError | null }> => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
        } as SignInRequest),
      });

      const data = await response.json();

      if (!response.ok) {
        const error: AuthError = {
          message: data.detail || data.message || 'Login failed',
          status: response.status,
        };
        
        toast({
          title: "Sign in failed",
          description: error.message,
          variant: "destructive",
        });
        
        return { error };
      }

      // Store user data from response
      sessionStorage.setItem('user_data', JSON.stringify(data));
      setUser(data);

      toast({
        title: "Welcome back!",
        description: "You've successfully signed in.",
      });
      window.location.href = '/onboarding';
      return { error: null };
    } catch (error) {
      const authError: AuthError = {
        message: error instanceof Error ? error.message : 'Network error occurred',
      };
      
      toast({
        title: "Sign in failed",
        description: authError.message,
        variant: "destructive",
      });
      
      return { error: authError };
    }
  };

  const signInWithProvider = async (provider: 'google' | 'github'): Promise<{ error: AuthError | null }> => {
    // For now, we'll show a message that OAuth is not implemented
    // You can implement this later when your backend supports OAuth
    const error: AuthError = {
      message: `${provider} authentication is not yet implemented`,
    };
    
    toast({
      title: "Not implemented",
      description: `${provider} authentication is coming soon!`,
      variant: "destructive",
    });
    
    return { error };
  };

  const signInAsGuest = () => {
    setIsGuest(true);
    setLoading(false);
    toast({
      title: "Browsing as Guest",
      description: "You can view all content but can't create or fork playbooks.",
    });
  };

  const signOut = async () => {
    // Clear session storage
    sessionStorage.removeItem('user_data');
    
    // Reset state
    setUser(null);
    setIsGuest(false);
    
    toast({
      title: "Signed out",
      description: "You've been successfully signed out.",
    });
  };

  return (
    <AuthContext.Provider value={{
      user,
      isGuest,
      signUp,
      signIn,
      signOut,
      signInWithProvider,
      signInAsGuest,
      loading
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
