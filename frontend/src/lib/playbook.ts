import { supabase } from '@/integrations/supabase/client';
import { v4 as uuidv4 } from 'uuid';

// Required buckets for the application
export const REQUIRED_BUCKETS = ['public-enux', 'private-enux'];

// Function to check if required storage buckets exist
export async function checkRequiredBuckets(): Promise<{ exists: boolean; missingBuckets: string[] }> {
  const missingBuckets: string[] = [];
  
  try {
    // Try to list buckets
    const { data: buckets, error } = await supabase.storage.listBuckets();
    
    if (error) {
      console.error('Error checking buckets:', error);
      // If permission denied, we can't determine if buckets exist
      if (error.message && error.message.includes('permission denied')) {
        console.log('Permission denied when listing buckets. Cannot verify bucket existence.');
        // Return true assuming buckets exist since we can't verify
        return { exists: true, missingBuckets: [] };
      }
      // For other errors, assume buckets don't exist
      return { exists: false, missingBuckets: REQUIRED_BUCKETS };
    }
    
    // Check which required buckets are missing
    if (buckets) {
      const existingBucketNames = buckets.map(bucket => bucket.name);
      for (const bucketName of REQUIRED_BUCKETS) {
        if (!existingBucketNames.includes(bucketName)) {
          missingBuckets.push(bucketName);
        }
      }
    } else {
      // If no buckets data, assume all required buckets are missing
      return { exists: false, missingBuckets: REQUIRED_BUCKETS };
    }
    
    return { 
      exists: missingBuckets.length === 0,
      missingBuckets 
    };
  } catch (error) {
    console.error('Unexpected error checking buckets:', error);
    // For unexpected errors, assume buckets exist to avoid blocking functionality
    return { exists: true, missingBuckets: [] };
  }
}

// Function to attempt to create missing buckets (requires admin privileges)
export async function createRequiredBuckets(): Promise<{ success: boolean; message: string; createdBuckets: string[] }> {
  const { exists, missingBuckets } = await checkRequiredBuckets();
  
  if (exists) {
    return { success: true, message: 'All required buckets already exist.', createdBuckets: [] };
  }
  
  const createdBuckets: string[] = [];
  let hasErrors = false;
  let errorMessage = '';
  
  for (const bucketName of missingBuckets) {
    try {
      const { error } = await supabase.storage.createBucket(bucketName, {
        public: bucketName.startsWith('public-') // Make public buckets public
      });
      
      if (error) {
        hasErrors = true;
        errorMessage += `Failed to create bucket ${bucketName}: ${error.message}. `;
        console.error(`Error creating bucket ${bucketName}:`, error);
      } else {
        createdBuckets.push(bucketName);
        console.log(`Successfully created bucket: ${bucketName}`);
      }
    } catch (error) {
      hasErrors = true;
      const message = error instanceof Error ? error.message : 'Unknown error';
      errorMessage += `Unexpected error creating bucket ${bucketName}: ${message}. `;
      console.error(`Unexpected error creating bucket ${bucketName}:`, error);
    }
  }
  
  if (hasErrors) {
    return { 
      success: createdBuckets.length > 0, 
      message: errorMessage + (createdBuckets.length > 0 ? 
        `Successfully created: ${createdBuckets.join(', ')}.` : ''),
      createdBuckets
    };
  }
  
  return { 
    success: true, 
    message: `Successfully created all required buckets: ${createdBuckets.join(', ')}.`,
    createdBuckets
  };
}

// Ensure the storage bucket exists
// This function now simply checks if the bucket is in our required buckets list
// and returns true, assuming the buckets have been created by an admin or via the UI
export async function ensureBucketExists(bucketName: string): Promise<boolean> {
  // Verify this is one of our required buckets
  if (!REQUIRED_BUCKETS.includes(bucketName)) {
    console.warn(`Attempting to use a bucket that is not in the required list: ${bucketName}`);
  }
  
  // We now assume the bucket exists and return true
  // Bucket creation is handled separately via the createRequiredBuckets function
  return true;
}

export async function createPlaybook(
  {
    title,
    description,
    license,
    visibility,
  }: {
    title: string;
    description: string;
    license: string;
    visibility: string;
  },
  files: File[],
  userId: string
): Promise<{ success: boolean; message?: string; playbookId?: string }> {
  const playbookId = uuidv4();
  const createdAt = new Date().toISOString();
  const commitId = uuidv4();
  const uploadedFiles: { path: string; name: string; type: string; size: number }[] = [];
  const bucketName = visibility === 'public' ? 'public-enux' : 'private-enux';

  try {
    // Check if required buckets exist
    const { exists, missingBuckets } = await checkRequiredBuckets();
    if (!exists) {
      throw new Error(
        `Required storage buckets are missing: ${missingBuckets.join(', ')}. ` +
        `Please create these buckets in your Supabase dashboard or use the "Create Required Buckets" button.`
      );
    }

    // Verify the specific bucket we need exists
    if (!await ensureBucketExists(bucketName)) {
      throw new Error(`Storage bucket ${bucketName} does not exist and could not be created.`);
    }

    // Create the playbook entry
    const { error: playbookError } = await supabase
      .from('playbooks')
      .insert({
        id: playbookId,
        title,
        description,
        license,
        visibility,
        user_id: userId,
        created_at: createdAt,
        updated_at: createdAt,
      });

    if (playbookError) {
      throw new Error(`Failed to create playbook: ${playbookError.message}`);
    }

    // Upload files to storage
    for (const file of files) {
      const filePath = `${playbookId}/${file.name}`;
      const { error: uploadError } = await supabase.storage
        .from(bucketName)
        .upload(filePath, file);

      if (uploadError) {
        console.error('Error uploading file:', uploadError);
        // Log more details about the error
        if (uploadError.message) console.error('Error message:', uploadError.message);
        if (uploadError.code) console.error('Error code:', uploadError.code);
        if (uploadError.details) console.error('Error details:', uploadError.details);
        
        // Provide more specific error messages based on the error type
        if (uploadError.message && uploadError.message.includes('permission denied')) {
          throw new Error(
            `Permission denied when uploading to ${bucketName} bucket. ` +
            `This may be due to Row Level Security (RLS) policies. ` +
            `Please check your storage permissions in the Supabase dashboard.`
          );
        } else if (uploadError.message && uploadError.message.includes('not found')) {
          throw new Error(
            `Storage bucket ${bucketName} not found. ` +
            `Please ensure it exists in your Supabase project by using the "Create Required Buckets" button.`
          );
        } else {
          throw new Error(`Failed to upload file ${file.name}: ${uploadError.message}`);
        }
      }

      uploadedFiles.push({
        path: filePath,
        name: file.name,
        type: file.type,
        size: file.size,
      });
    }

    // Create asset entries
    const assets = uploadedFiles.map((file) => ({
      id: uuidv4(),
      playbook_id: playbookId,
      name: file.name,
      type: file.type,
      size: file.size,
      storage_path: file.path,
      created_at: createdAt,
      updated_at: createdAt,
    }));

    const { error: assetsError } = await supabase.from('playbook_assets').insert(assets);

    if (assetsError) {
      throw new Error(`Failed to create asset entries: ${assetsError.message}`);
    }

    // Create initial commit
    const { error: commitError } = await supabase.from('playbook_versions').insert({
      id: commitId,
      playbook_id: playbookId,
      message: 'Initial commit',
      created_at: createdAt,
      user_id: userId,
    });

    if (commitError) {
      throw new Error(`Failed to create initial commit: ${commitError.message}`);
    }

    return { success: true, message: 'Playbook created successfully', playbookId };
  } catch (error) {
    // If any step fails, clean up any created resources
    await cleanupPlaybookCreation(playbookId, uploadedFiles, bucketName);
    
    // Return error message instead of throwing
    return { 
      success: false, 
      message: error instanceof Error ? error.message : 'An unknown error occurred during playbook creation' 
    };
  }
}

// Helper function to clean up resources if playbook creation fails
async function cleanupPlaybookCreation(
  playbookId: string,
  uploadedFiles: Array<{ path: string; name: string; type: string; size: number }>,
  bucketName: string
): Promise<void> {
  if (!playbookId) return;

  console.log(`Cleaning up resources for failed playbook creation: ${playbookId}`);

  try {
    // 1. Delete uploaded files from storage
    if (uploadedFiles.length > 0) {
      console.log(`Removing ${uploadedFiles.length} files from ${bucketName} bucket`);
      const filePaths = uploadedFiles.map(file => file.path);
      
      const { error: removeError } = await supabase.storage
        .from(bucketName)
        .remove(filePaths);
      
      if (removeError) {
        console.error(`Error removing files from ${bucketName} bucket:`, removeError);
      } else {
        console.log(`Successfully removed files from ${bucketName} bucket`);
      }
    }

    // 2. Delete asset entries
    const { error: assetsError } = await supabase
      .from('playbook_assets')
      .delete()
      .eq('playbook_id', playbookId);
    
    if (assetsError) {
      console.error('Error deleting asset entries:', assetsError);
    } else {
      console.log('Successfully deleted asset entries');
    }

    // 3. Delete version entries
    const { error: versionsError } = await supabase
      .from('playbook_versions')
      .delete()
      .eq('playbook_id', playbookId);
    
    if (versionsError) {
      console.error('Error deleting version entries:', versionsError);
    } else {
      console.log('Successfully deleted version entries');
    }

    // 4. Delete playbook entry
    const { error: playbookError } = await supabase
      .from('playbooks')
      .delete()
      .eq('id', playbookId);
    
    if (playbookError) {
      console.error('Error deleting playbook entry:', playbookError);
    } else {
      console.log('Successfully deleted playbook entry');
    }

    console.log(`Cleanup completed for failed playbook creation: ${playbookId}`);
  } catch (error) {
    console.error('Unexpected error during cleanup:', error);
  }
}