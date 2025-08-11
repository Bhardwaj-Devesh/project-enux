import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/hooks/useAuth";
import Index from "./pages/Index";
import SearchResults from "./pages/SearchResults";
import Onboarding from "./pages/Onboarding";
import PlaybookDetail from "./pages/PlaybookDetail";
import NotFound from "./pages/NotFound";
import CreatePlaybook from './pages/CreatePlaybook';
import BlogEditor from './pages/BlogEditor';
import MyPlaybooks from './pages/MyPlaybooks';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import Community from './pages/Community';

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/search" element={<SearchResults />} />
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="/playbook/:id" element={<PlaybookDetail />} />
            <Route path="/create" element={<CreatePlaybook />} />
            <Route path="/blog-editor" element={<BlogEditor />} />
            <Route path="/my-playbooks" element={<MyPlaybooks />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/community" element={<Community />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
