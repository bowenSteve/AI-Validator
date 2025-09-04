import React, { useState, useCallback } from 'react';
import { 
  ImageUploadSection, 
  ImageDataSection, 
  ValidationSection 
} from './components';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function Dashboard({ isDark }) {
  // State for images - now arrays to support multiple images
  const [mainImages, setMainImages] = useState([]);
  const [secondaryImages, setSecondaryImages] = useState([]);
  
  // Loading states
  const [isMainUploading, setIsMainUploading] = useState(false);
  const [isSecondaryUploading, setIsSecondaryUploading] = useState(false);

  // Validation states
  const [validationResult, setValidationResult] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [validationError, setValidationError] = useState(null);

  // Upload main image via form data (for file input and drag & drop)
  const uploadMainImage = async (file) => {
    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await fetch(`${API_URL}/api/uploads/main/upload`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Upload failed');
      }

      return result;
    } catch (error) {
      console.error('Main image upload error:', error);
      throw error;
    }
  };

  // Upload secondary image via form data (for file input and drag & drop)
  const uploadSecondaryImage = async (file) => {
    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await fetch(`${API_URL}/api/uploads/secondary/upload`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Upload failed');
      }

      return result;
    } catch (error) {
      console.error('Secondary image upload error:', error);
      throw error;
    }
  };

  // Upload main image via base64 (for paste functionality)
  const uploadMainImageBase64 = async (base64Data, filename = null) => {
    try {
      const response = await fetch(`${API_URL}/api/uploads/main/upload/base64`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_data: base64Data,
          filename: filename || `main-pasted-${Date.now()}.png`
        }),
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Upload failed');
      }

      return result;
    } catch (error) {
      console.error('Main image base64 upload error:', error);
      throw error;
    }
  };

  // Upload secondary image via base64 (for paste functionality)
  const uploadSecondaryImageBase64 = async (base64Data, filename = null) => {
    try {
      const response = await fetch(`${API_URL}/api/uploads/secondary/upload/base64`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_data: base64Data,
          filename: filename || `secondary-pasted-${Date.now()}.png`
        }),
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Upload failed');
      }

      return result;
    } catch (error) {
      console.error('Secondary image base64 upload error:', error);
      throw error;
    }
  };

  // Handle main image upload
  const handleMainImageUpload = useCallback(async (file) => {
    if (file && file.type.startsWith('image/')) {
      setIsMainUploading(true);
      try {
        const result = await uploadMainImage(file);

        // Create image data for local preview
        const reader = new FileReader();
        reader.onload = (e) => {
          const imageData = {
            file: file,
            url: e.target.result,
            name: file.name,
            upload_id: result.upload_id,
            file_id: result.file_id,
            file_size: file.size,
            type: 'main',
            uploaded_at: new Date().toISOString(),
            // Add Gemini processing data
            gemini_processing: result.gemini_processing || null,
            extracted_text: result.gemini_processing?.extracted_text || ''
          };
          
          setMainImages(prev => [...prev, imageData]);
        };
        reader.readAsDataURL(file);

        console.log('Main image uploaded successfully:', result);
        
      } catch (error) {
        console.error('Main image upload failed:', error);
        alert(`Main image upload failed: ${error.message}`);
      } finally {
        setIsMainUploading(false);
      }
    }
  }, []);

  // Handle secondary image upload
  const handleSecondaryImageUpload = useCallback(async (file) => {
    if (file && file.type.startsWith('image/')) {
      setIsSecondaryUploading(true);
      try {
        const result = await uploadSecondaryImage(file);

        // Create image data for local preview
        const reader = new FileReader();
        reader.onload = (e) => {
          const imageData = {
            file: file,
            url: e.target.result,
            name: file.name,
            upload_id: result.upload_id,
            file_id: result.file_id,
            file_size: file.size,
            type: 'secondary',
            uploaded_at: new Date().toISOString(),
            // Add Gemini processing data
            gemini_processing: result.gemini_processing || null,
            extracted_text: result.gemini_processing?.extracted_text || ''
          };
          
          setSecondaryImages(prev => [...prev, imageData]);
        };
        reader.readAsDataURL(file);

        console.log('Secondary image uploaded successfully:', result);
        
      } catch (error) {
        console.error('Secondary image upload failed:', error);
        alert(`Secondary image upload failed: ${error.message}`);
      } finally {
        setIsSecondaryUploading(false);
      }
    }
  }, []);

  // Handle main image upload via base64 (for paste functionality)
  const handleMainImageBase64Upload = useCallback(async (base64Data, filename) => {
    try {
      const result = await uploadMainImageBase64(base64Data, filename);
      
      // Convert base64 to blob for preview
      const response = await fetch(base64Data);
      const blob = await response.blob();
      
      const imageData = {
        file: new File([blob], filename, { type: blob.type }),
        url: base64Data,
        name: filename,
        upload_id: result.upload_id,
        file_id: result.file_id,
        file_size: blob.size,
        type: 'main',
        uploaded_at: new Date().toISOString(),
        gemini_processing: result.gemini_processing || null,
        extracted_text: result.gemini_processing?.extracted_text || ''
      };
      
      setMainImages(prev => [...prev, imageData]);
      console.log('Main image pasted and uploaded successfully:', result);
      
    } catch (error) {
      console.error('Main image base64 upload failed:', error);
      throw error;
    }
  }, []);

  // Handle secondary image upload via base64 (for paste functionality)
  const handleSecondaryImageBase64Upload = useCallback(async (base64Data, filename) => {
    try {
      const result = await uploadSecondaryImageBase64(base64Data, filename);
      
      // Convert base64 to blob for preview
      const response = await fetch(base64Data);
      const blob = await response.blob();
      
      const imageData = {
        file: new File([blob], filename, { type: blob.type }),
        url: base64Data,
        name: filename,
        upload_id: result.upload_id,
        file_id: result.file_id,
        file_size: blob.size,
        type: 'secondary',
        uploaded_at: new Date().toISOString(),
        gemini_processing: result.gemini_processing || null,
        extracted_text: result.gemini_processing?.extracted_text || ''
      };
      
      setSecondaryImages(prev => [...prev, imageData]);
      console.log('Secondary image pasted and uploaded successfully:', result);
      
    } catch (error) {
      console.error('Secondary image base64 upload failed:', error);
      throw error;
    }
  }, []);

  // Clear all images
  const clearAllImages = useCallback(() => {
    setMainImages([]);
    setSecondaryImages([]);
    setValidationResult(null);
    setValidationError(null);
  }, []);

  // Validate images with Gemini
  const validateImages = useCallback(async () => {
    if (mainImages.length === 0 || secondaryImages.length === 0) {
      setValidationError('Both image sections must have at least one image before validation');
      return;
    }

    // Get all upload IDs from images that were successfully processed
    const mainUploadIds = mainImages
      .filter(img => img.upload_id && img.gemini_processing?.success)
      .map(img => img.upload_id);
      
    const secondaryUploadIds = secondaryImages
      .filter(img => img.upload_id && img.gemini_processing?.success)
      .map(img => img.upload_id);

    if (mainUploadIds.length === 0) {
      setValidationError('No successfully processed main images found');
      return;
    }

    if (secondaryUploadIds.length === 0) {
      setValidationError('No successfully processed secondary images found');
      return;
    }

    setIsValidating(true);
    setValidationError(null);
    setValidationResult(null);

    try {
      const response = await fetch(`${API_URL}/api/validation/compare/gemini`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          main_upload_ids: mainUploadIds,
          secondary_upload_ids: secondaryUploadIds,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Validation failed');
      }

      setValidationResult(result.validation_result);
      console.log('Multi-image validation completed:', result);

    } catch (error) {
      console.error('Validation error:', error);
      setValidationError(error.message || 'Validation failed. Please try again.');
    } finally {
      setIsValidating(false);
    }
  }, [mainImages, secondaryImages]);

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Dashboard
        </h1>
        <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>
          Upload and compare your screenshots
        </p>
      </div>

      {/* Image Upload Sections */}
      <div className="grid md:grid-cols-2 gap-8">
        <ImageUploadSection
          title="Util Screenshots"
          images={mainImages}
          setImages={setMainImages}
          isUploading={isMainUploading}
          setIsUploading={setIsMainUploading}
          uploadImageHandler={handleMainImageUpload}
          uploadImageBase64Handler={handleMainImageBase64Upload}
          inputId="main-file-input"
          isDark={isDark}
        />
        
        <ImageUploadSection
          title="Website Screenshots"
          images={secondaryImages}
          setImages={setSecondaryImages}
          isUploading={isSecondaryUploading}
          setIsUploading={setIsSecondaryUploading}
          uploadImageHandler={handleSecondaryImageUpload}
          uploadImageBase64Handler={handleSecondaryImageBase64Upload}
          inputId="secondary-file-input"
          isDark={isDark}
        />
      </div>

      {/* Image Data Section */}
      <ImageDataSection
        mainImages={mainImages}
        secondaryImages={secondaryImages}
        isDark={isDark}
      />

      {/* Validation Section */}
      <ValidationSection
        mainImages={mainImages}
        secondaryImages={secondaryImages}
        isValidating={isValidating}
        validationResult={validationResult}
        validationError={validationError}
        onValidate={validateImages}
        onClearAll={clearAllImages}
        isDark={isDark}
      />
    </div>
  );
}

export default Dashboard;