import React, { useState, useCallback } from 'react';
import { Upload, X, Image, CheckSquare, AlertTriangle } from 'lucide-react';
import GeminiValidationResults from '../components/GeminiValidationResults';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function Dashboard({isDark}) {
  // Separate states for main and secondary images
  const [mainImage, setMainImage] = useState(null);
  const [secondaryImage, setSecondaryImage] = useState(null);
  
  // Separate loading states
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
          
          setMainImage(imageData);
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
          
          setSecondaryImage(imageData);
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

  // Handle main image paste
  const handleMainImagePaste = useCallback(async (e) => {
    e.preventDefault();
    const items = Array.from(e.clipboardData.items);
    
    for (let item of items) {
      if (item.type.indexOf('image') !== -1) {
        const blob = item.getAsFile();
        if (blob) {
          setIsMainUploading(true);
          try {
            // Convert blob to base64
            const reader = new FileReader();
            reader.onload = async (e) => {
              const base64Data = e.target.result;
              const filename = `main-pasted-${Date.now()}.png`;
              
              const result = await uploadMainImageBase64(base64Data, filename);

              // Create image data for local preview
              const imageData = {
                file: new File([blob], filename, { type: blob.type }),
                url: base64Data,
                name: filename,
                upload_id: result.upload_id,
                file_id: result.file_id,
                file_size: blob.size,
                type: 'main',
                uploaded_at: new Date().toISOString(),
                // Add Gemini processing data
                gemini_processing: result.gemini_processing || null,
                extracted_text: result.gemini_processing?.extracted_text || ''
              };
              
              setMainImage(imageData);
              console.log('Main image pasted and uploaded successfully:', result);
              setIsMainUploading(false);
            };
            reader.readAsDataURL(blob);
            
          } catch (error) {
            console.error('Main image paste upload failed:', error);
            alert(`Main image paste upload failed: ${error.message}`);
            setIsMainUploading(false);
          }
        }
        break;
      }
    }
  }, []);

  // Handle secondary image paste
  const handleSecondaryImagePaste = useCallback(async (e) => {
    e.preventDefault();
    const items = Array.from(e.clipboardData.items);
    
    for (let item of items) {
      if (item.type.indexOf('image') !== -1) {
        const blob = item.getAsFile();
        if (blob) {
          setIsSecondaryUploading(true);
          try {
            // Convert blob to base64
            const reader = new FileReader();
            reader.onload = async (e) => {
              const base64Data = e.target.result;
              const filename = `secondary-pasted-${Date.now()}.png`;
              
              const result = await uploadSecondaryImageBase64(base64Data, filename);

              // Create image data for local preview
              const imageData = {
                file: new File([blob], filename, { type: blob.type }),
                url: base64Data,
                name: filename,
                upload_id: result.upload_id,
                file_id: result.file_id,
                file_size: blob.size,
                type: 'secondary',
                uploaded_at: new Date().toISOString(),
                // Add Gemini processing data
                gemini_processing: result.gemini_processing || null,
                extracted_text: result.gemini_processing?.extracted_text || ''
              };
              
              setSecondaryImage(imageData);
              console.log('Secondary image pasted and uploaded successfully:', result);
              setIsSecondaryUploading(false);
            };
            reader.readAsDataURL(blob);
            
          } catch (error) {
            console.error('Secondary image paste upload failed:', error);
            alert(`Secondary image paste upload failed: ${error.message}`);
            setIsSecondaryUploading(false);
          }
        }
        break;
      }
    }
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  // Separate drop handlers
  const handleMainDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleMainImageUpload(files[0]);
    }
  }, [handleMainImageUpload]);

  const handleSecondaryDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleSecondaryImageUpload(files[0]);
    }
  }, [handleSecondaryImageUpload]);

  // Separate file input handlers
  const handleMainFileInput = useCallback((e) => {
    const file = e.target.files[0];
    if (file) {
      handleMainImageUpload(file);
    }
  }, [handleMainImageUpload]);

  const handleSecondaryFileInput = useCallback((e) => {
    const file = e.target.files[0];
    if (file) {
      handleSecondaryImageUpload(file);
    }
  }, [handleSecondaryImageUpload]);

  // Separate remove handlers
  const removeMainImage = useCallback(() => {
    setMainImage(null);
  }, []);

  const removeSecondaryImage = useCallback(() => {
    setSecondaryImage(null);
  }, []);

  // Clear all images
  const clearAllImages = useCallback(() => {
    setMainImage(null);
    setSecondaryImage(null);
    setValidationResult(null);
    setValidationError(null);
  }, []);

  // Validate images with Gemini
  const validateImages = useCallback(async () => {
    if (!mainImage || !secondaryImage) {
      setValidationError('Both images must be uploaded before validation');
      return;
    }

    if (!mainImage.upload_id || !secondaryImage.upload_id) {
      setValidationError('Images must be successfully processed before validation');
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
          main_upload_id: mainImage.upload_id,
          secondary_upload_id: secondaryImage.upload_id,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Validation failed');
      }

      setValidationResult(result.validation_result);
      console.log('Validation completed:', result);

    } catch (error) {
      console.error('Validation error:', error);
      setValidationError(error.message || 'Validation failed. Please try again.');
    } finally {
      setIsValidating(false);
    }
  }, [mainImage, secondaryImage]);

  // Main Upload Field Component
  const MainUploadField = () => (
    <div className="flex flex-col space-y-3">
      <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
        Util Screenshot
      </label>
      
      {!mainImage ? (
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer focus:outline-none focus:ring-2 ${
            isDark 
              ? 'border-gray-600 hover:border-gray-500 bg-gray-800 focus:ring-cyan-500' 
              : 'border-gray-300 hover:border-gray-400 bg-white focus:ring-blue-500'
          } ${isMainUploading ? 'opacity-50 pointer-events-none' : ''}`}
          onDragOver={handleDragOver}
          onDrop={handleMainDrop}
          onPaste={handleMainImagePaste}
          onClick={() => !isMainUploading && document.getElementById('main-file-input').click()}
          tabIndex={0}
        >
          <Upload className={`mx-auto h-12 w-12 ${isDark ? 'text-gray-500' : 'text-gray-400'} ${isMainUploading ? 'animate-pulse' : ''}`} />
          <div className="mt-4">
            <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>
              {isMainUploading ? (
                <span className="font-medium">Uploading main image...</span>
              ) : (
                <>
                  <span className={`font-medium ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>Click to upload</span>, drag and drop, or <span className={`font-medium ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>paste (Ctrl+V)</span>
                </>
              )}
            </p>
            <p className={`text-xs mt-1 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>PNG, JPG, GIF up to 10MB</p>
          </div>
          
          <input
            id="main-file-input"
            type="file"
            className="hidden"
            accept="image/*"
            onChange={handleMainFileInput}
            disabled={isMainUploading}
          />
        </div>
      ) : (
        <div className={`relative border rounded-lg p-4 ${
          isDark 
            ? 'border-gray-600 bg-gray-800' 
            : 'border-gray-200 bg-white'
        }`}>
          <button
            onClick={removeMainImage}
            className={`absolute top-2 right-2 z-10 p-1 rounded-full transition-colors ${
              isDark 
                ? 'bg-red-900 hover:bg-red-800 text-red-400' 
                : 'bg-red-100 hover:bg-red-200 text-red-600'
            }`}
          >
            <X size={16} />
          </button>
          
          <div className="flex items-center space-x-4">
            <div className="flex-shrink-0">
              <img
                src={mainImage.url}
                alt={mainImage.name}
                className="h-20 w-20 object-cover rounded border"
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className={`text-sm font-medium truncate ${isDark ? 'text-gray-100' : 'text-gray-900'}`}>
                {mainImage.name}
              </p>
              <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                {(mainImage.file_size / 1024 / 1024).toFixed(2)} MB
              </p>
              {mainImage.upload_id && (
                <p className={`text-xs ${isDark ? 'text-green-400' : 'text-green-600'}`}>
                  ✓ Main image uploaded successfully
                </p>
              )}
            </div>
            <div className="flex-shrink-0">
              <Image className={`h-5 w-5 ${isDark ? 'text-green-400' : 'text-green-500'}`} />
            </div>
          </div>
        </div>
      )}
    </div>
  );

  // Secondary Upload Field Component
  const SecondaryUploadField = () => (
    <div className="flex flex-col space-y-3">
      <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
        Website Screenshot
      </label>
      
      {!secondaryImage ? (
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer focus:outline-none focus:ring-2 ${
            isDark 
              ? 'border-gray-600 hover:border-gray-500 bg-gray-800 focus:ring-cyan-500' 
              : 'border-gray-300 hover:border-gray-400 bg-white focus:ring-blue-500'
          } ${isSecondaryUploading ? 'opacity-50 pointer-events-none' : ''}`}
          onDragOver={handleDragOver}
          onDrop={handleSecondaryDrop}
          onPaste={handleSecondaryImagePaste}
          onClick={() => !isSecondaryUploading && document.getElementById('secondary-file-input').click()}
          tabIndex={0}
        >
          <Upload className={`mx-auto h-12 w-12 ${isDark ? 'text-gray-500' : 'text-gray-400'} ${isSecondaryUploading ? 'animate-pulse' : ''}`} />
          <div className="mt-4">
            <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>
              {isSecondaryUploading ? (
                <span className="font-medium">Uploading secondary image...</span>
              ) : (
                <>
                  <span className={`font-medium ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>Click to upload</span>, drag and drop, or <span className={`font-medium ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>paste (Ctrl+V)</span>
                </>
              )}
            </p>
            <p className={`text-xs mt-1 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>PNG, JPG, GIF up to 10MB</p>
          </div>
          
          <input
            id="secondary-file-input"
            type="file"
            className="hidden"
            accept="image/*"
            onChange={handleSecondaryFileInput}
            disabled={isSecondaryUploading}
          />
        </div>
      ) : (
        <div className={`relative border rounded-lg p-4 ${
          isDark 
            ? 'border-gray-600 bg-gray-800' 
            : 'border-gray-200 bg-white'
        }`}>
          <button
            onClick={removeSecondaryImage}
            className={`absolute top-2 right-2 z-10 p-1 rounded-full transition-colors ${
              isDark 
                ? 'bg-red-900 hover:bg-red-800 text-red-400' 
                : 'bg-red-100 hover:bg-red-200 text-red-600'
            }`}
          >
            <X size={16} />
          </button>
          
          <div className="flex items-center space-x-4">
            <div className="flex-shrink-0">
              <img
                src={secondaryImage.url}
                alt={secondaryImage.name}
                className="h-20 w-20 object-cover rounded border"
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className={`text-sm font-medium truncate ${isDark ? 'text-gray-100' : 'text-gray-900'}`}>
                {secondaryImage.name}
              </p>
              <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                {(secondaryImage.file_size / 1024 / 1024).toFixed(2)} MB
              </p>
              {secondaryImage.upload_id && (
                <p className={`text-xs ${isDark ? 'text-green-400' : 'text-green-600'}`}>
                  ✓ Secondary image uploaded successfully
                </p>
              )}
            </div>
            <div className="flex-shrink-0">
              <Image className={`h-5 w-5 ${isDark ? 'text-green-400' : 'text-green-500'}`} />
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Dashboard</h1>
        <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>Upload and compare your screenshots</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        <MainUploadField />
        <SecondaryUploadField />
      </div>

      {/* Image Data Fields Section */}
      {(mainImage || secondaryImage) && (
        <div className={`mt-8 pt-8 border-t ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
          <h2 className={`text-xl font-semibold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Image Data Fields
          </h2>
          
          <div className="grid md:grid-cols-2 gap-8">
            {/* Main Image Data */}
            {mainImage && (
              <div className={`p-4 rounded-lg border ${
                isDark 
                  ? 'border-gray-600 bg-gray-800' 
                  : 'border-gray-200 bg-gray-50'
              }`}>
                <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>
                  Main Screenshot Data
                </h3>
                
                <div className="space-y-3">
                  <div>
                    <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      File Information:
                    </label>
                    <div className={`mt-1 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                      <p>Name: {mainImage.name}</p>
                      <p>Size: {(mainImage.file_size / 1024 / 1024).toFixed(2)} MB</p>
                      <p>Upload ID: {mainImage.upload_id || 'N/A'}</p>
                      <p>Type: {mainImage.type}</p>
                      <p>Uploaded: {new Date(mainImage.uploaded_at).toLocaleString()}</p>
                    </div>
                  </div>
                  
                  <div>
                    <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      Processing Status:
                    </label>
                    <div className={`mt-1 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                      {mainImage.gemini_processing ? (
                        <div className="space-y-1">
                          <p className={mainImage.gemini_processing.success ? 'text-green-500' : 'text-red-500'}>
                            ● {mainImage.gemini_processing.success ? 'Text extraction successful' : 'Text extraction failed'}
                          </p>
                          {mainImage.gemini_processing.error && (
                            <p className="text-red-500">Error: {mainImage.gemini_processing.error}</p>
                          )}
                          {mainImage.gemini_processing.processing_time && (
                            <p>Processing attempts: {mainImage.gemini_processing.processing_time}</p>
                          )}
                        </div>
                      ) : (
                        <p className="text-yellow-500">● Processing status unknown</p>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      Extracted Text:
                    </label>
                    <div className={`mt-2 p-3 rounded border text-xs max-h-40 overflow-y-auto ${
                      isDark 
                        ? 'border-gray-600 bg-gray-700 text-gray-300' 
                        : 'border-gray-200 bg-white text-gray-700'
                    }`}>
                      {mainImage.extracted_text ? (
                        <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed">
                          {mainImage.extracted_text}
                        </pre>
                      ) : (
                        <p className={`italic ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                          {mainImage.gemini_processing?.success === false 
                            ? 'Text extraction failed' 
                            : 'No text extracted or processing in progress...'}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Secondary Image Data */}
            {secondaryImage && (
              <div className={`p-4 rounded-lg border ${
                isDark 
                  ? 'border-gray-600 bg-gray-800' 
                  : 'border-gray-200 bg-gray-50'
              }`}>
                <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>
                  Secondary Screenshot Data
                </h3>
                
                <div className="space-y-3">
                  <div>
                    <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      File Information:
                    </label>
                    <div className={`mt-1 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                      <p>Name: {secondaryImage.name}</p>
                      <p>Size: {(secondaryImage.file_size / 1024 / 1024).toFixed(2)} MB</p>
                      <p>Upload ID: {secondaryImage.upload_id || 'N/A'}</p>
                      <p>Type: {secondaryImage.type}</p>
                      <p>Uploaded: {new Date(secondaryImage.uploaded_at).toLocaleString()}</p>
                    </div>
                  </div>
                  
                  <div>
                    <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      Processing Status:
                    </label>
                    <div className={`mt-1 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                      {secondaryImage.gemini_processing ? (
                        <div className="space-y-1">
                          <p className={secondaryImage.gemini_processing.success ? 'text-green-500' : 'text-red-500'}>
                            ● {secondaryImage.gemini_processing.success ? 'Text extraction successful' : 'Text extraction failed'}
                          </p>
                          {secondaryImage.gemini_processing.error && (
                            <p className="text-red-500">Error: {secondaryImage.gemini_processing.error}</p>
                          )}
                          {secondaryImage.gemini_processing.processing_time && (
                            <p>Processing attempts: {secondaryImage.gemini_processing.processing_time}</p>
                          )}
                        </div>
                      ) : (
                        <p className="text-yellow-500">● Processing status unknown</p>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      Extracted Text:
                    </label>
                    <div className={`mt-2 p-3 rounded border text-xs max-h-40 overflow-y-auto ${
                      isDark 
                        ? 'border-gray-600 bg-gray-700 text-gray-300' 
                        : 'border-gray-200 bg-white text-gray-700'
                    }`}>
                      {secondaryImage.extracted_text ? (
                        <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed">
                          {secondaryImage.extracted_text}
                        </pre>
                      ) : (
                        <p className={`italic ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                          {secondaryImage.gemini_processing?.success === false 
                            ? 'Text extraction failed' 
                            : 'No text extracted or processing in progress...'}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Action buttons when both images are present */}
      {mainImage && secondaryImage && (
        <div className={`mt-8 pt-8 border-t ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
          <div className="flex justify-center space-x-4">
            <button 
              onClick={validateImages}
              disabled={isValidating || !mainImage?.upload_id || !secondaryImage?.upload_id}
              className={`px-6 py-2 text-white font-medium rounded-lg transition-colors flex items-center space-x-2 ${
                isValidating || !mainImage?.upload_id || !secondaryImage?.upload_id
                  ? 'bg-gray-400 cursor-not-allowed'
                  : isDark 
                    ? 'bg-cyan-600 hover:bg-cyan-700' 
                    : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isValidating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <CheckSquare className="w-4 h-4" />
                  <span>Validate Transfer</span>
                </>
              )}
            </button>
            
            <button 
              onClick={clearAllImages}
              className={`px-6 py-2 font-medium rounded-lg transition-colors ${
                isDark 
                  ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' 
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              }`}
            >
              Clear All Images
            </button>
          </div>
        </div>
      )}

      {/* Validation Error Display */}
      {validationError && (
        <div className={`mt-8 p-4 rounded-lg border-l-4 border-red-500 ${
          isDark ? 'bg-red-900 bg-opacity-20' : 'bg-red-50'
        }`}>
          <div className="flex items-start">
            <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
            <div>
              <h3 className={`text-sm font-medium ${isDark ? 'text-red-400' : 'text-red-800'}`}>
                Validation Error
              </h3>
              <p className={`mt-1 text-sm ${isDark ? 'text-red-300' : 'text-red-700'}`}>
                {validationError}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Validation Results */}
      <GeminiValidationResults 
        validationResult={validationResult}
        isDark={isDark}
        isLoading={isValidating}
      />
    </div>
  );
}

export default Dashboard;