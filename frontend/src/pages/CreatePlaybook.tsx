import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { UploadCloud, FileText, File, XCircle, AlertTriangle, CheckCircle, Tag, ArrowRight } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Navigation } from '@/components/Navigation';

interface PlaybookFormData {
  title: string;
  description: string;
  tags: string[];
  license: string;
  visibility: 'public' | 'private';
  files: File[];
}

export default function CreatePlaybook() {
  const [formData, setFormData] = useState<PlaybookFormData>({
    title: '',
    description: '',
    tags: [],
    license: '',
    visibility: 'private',
    files: []
  });
  const [tagInput, setTagInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const { user } = useAuth();
  const navigate = useNavigate();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFormData(prev => ({
      ...prev,
      files: [...prev.files, ...acceptedFiles]
    }));
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    noClick: true,
  });

  const handleFileBrowseClick = () => {
    const inputElement = document.getElementById('file-upload-input');
    if (inputElement) {
      inputElement.click();
    }
  };

  const handleRemoveFile = (fileToRemove: File) => {
    setFormData(prev => ({
      ...prev,
      files: prev.files.filter(file => file !== fileToRemove)
    }));
  };

  const handleAddTag = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      if (!formData.tags.includes(tagInput.trim())) {
        setFormData(prev => ({
          ...prev,
          tags: [...prev.tags, tagInput.trim()]
        }));
      }
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleNext = () => {
    if (!formData.title || !formData.description) {
      toast({
        title: 'Missing required fields',
        description: 'Please fill in title and description.',
        variant: 'destructive',
      });
      return;
    }

    // Store form data in sessionStorage and navigate to blog editor
    sessionStorage.setItem('playbook_form_data', JSON.stringify(formData));
    navigate('/blog-editor');
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold">Create a New Playbook</CardTitle>
            <CardDescription className="text-muted-foreground">
              Build your playbook by adding metadata and uploading files. You'll write the blog content in the next step.
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form className="space-y-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Basic Information</h3>
                
                <div>
                  <Label htmlFor="title">Title *</Label>
                  <Input
                    id="title"
                    placeholder="e.g., B2B SaaS Growth Hacking Playbook"
                    value={formData.title}
                    onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="description">Description *</Label>
                  <Textarea
                    id="description"
                    placeholder="A detailed description of your playbook..."
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    rows={4}
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="tags">Tags</Label>
                  <div className="space-y-2">
                    <Input
                      id="tags"
                      placeholder="Press Enter to add tags..."
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyPress={handleAddTag}
                    />
                    {formData.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {formData.tags.map((tag, index) => (
                          <Badge key={index} variant="secondary" className="flex items-center gap-1">
                            <Tag className="h-3 w-3" />
                            {tag}
                            <button
                              type="button"
                              onClick={() => handleRemoveTag(tag)}
                              className="ml-1 hover:text-destructive"
                            >
                              ×
                            </button>
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* File Upload Section */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Upload Documents</h3>
                
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    isDragActive ? 'border-primary bg-muted' : 'border-gray-300 bg-background'
                  }`}
                >
                  <input id="file-upload-input" {...getInputProps()} />
                  <UploadCloud className="mx-auto h-12 w-12 text-gray-400" />
                  <p className="mt-2 text-sm text-gray-600">
                    {isDragActive ? 'Drop the files here...' : 'Drag & drop files here, or'}
                  </p>
                  <Button type="button" variant="outline" className="mt-2" onClick={handleFileBrowseClick}>
                    Browse files
                  </Button>
                </div>

                {formData.files.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-md font-medium mb-2">Files to Upload:</h4>
                    <ul className="space-y-2">
                      {formData.files.map((file, index) => (
                        <li key={index} className="flex items-center justify-between p-2 border rounded-md">
                          <div className="flex items-center">
                            <File className="h-5 w-5 mr-2 text-gray-500" />
                            <span>{file.name}</span>
                            <span className="ml-2 text-sm text-muted-foreground">
                              ({(file.size / 1024).toFixed(2)} KB)
                            </span>
                          </div>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveFile(file)}
                            className="text-red-500 hover:text-red-700"
                          >
                            <XCircle className="h-4 w-4" />
                          </Button>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Settings */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Settings</h3>
                
                <div>
                  <Label htmlFor="license">License</Label>
                  <Select value={formData.license} onValueChange={(value) => setFormData(prev => ({ ...prev, license: value }))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a license" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CC-BY">Creative Commons Attribution (CC-BY)</SelectItem>
                      <SelectItem value="MIT">MIT License</SelectItem>
                      <SelectItem value="Apache-2.0">Apache License 2.0</SelectItem>
                      <SelectItem value="GPL-3.0">GNU General Public License v3.0</SelectItem>
                      <SelectItem value="Custom">Custom License</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Visibility</Label>
                  <RadioGroup 
                    value={formData.visibility} 
                    onValueChange={(value) => setFormData(prev => ({ ...prev, visibility: value as 'public' | 'private' }))} 
                    className="flex space-x-4 mt-2"
                  >
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="public" id="public" />
                      <Label htmlFor="public">Public</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="private" id="private" />
                      <Label htmlFor="private">Private</Label>
                    </div>
                  </RadioGroup>
                </div>
              </div>

              <div className="flex justify-end pt-6">
                <Button 
                  type="button" 
                  onClick={handleNext}
                  disabled={!formData.title || !formData.description}
                  className="flex items-center gap-2"
                >
                  Next: Write Blog
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
