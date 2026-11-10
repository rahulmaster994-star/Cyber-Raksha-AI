import React, { useState } from 'react';
import { MessageSquare, CheckCircle, AlertTriangle, X } from 'lucide-react';
import { apiService } from '../services/api';

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  targetIdentifier?: string;
  analysisId?: number;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  isOpen,
  onClose,
  targetIdentifier,
  analysisId,
}) => {
  const [category, setCategory] = useState<string>('FALSE_POSITIVE');
  const [explanation, setExplanation] = useState<string>('');
  const [label, setLabel] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitSuccess, setSubmitSuccess] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);

    const res = await apiService.submitFeedback({
      analysis_id: analysisId,
      target_identifier: targetIdentifier,
      feedback_category: category,
      user_explanation: explanation,
      user_provided_label: label,
    });

    setIsSubmitting(false);
    if (res.error) {
      setErrorMsg(res.error);
    } else {
      setSubmitSuccess(true);
      setTimeout(() => {
        setSubmitSuccess(false);
        onClose();
      }, 2500);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg rounded-xl border border-[#1E2E5C] bg-[#0A0F1D] p-6 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Detection Feedback</h3>
            <p className="text-xs text-gray-400">Help improve accuracy through human review</p>
          </div>
        </div>

        {submitSuccess ? (
          <div className="py-8 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto border border-emerald-500/30">
              <CheckCircle className="w-6 h-6" />
            </div>
            <h4 className="text-base font-medium text-white">Feedback Submitted</h4>
            <p className="text-xs text-gray-400 max-w-sm mx-auto">
              Your report has been queued for human review. In accordance with safety policies, feedback does not trigger automatic model changes.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {targetIdentifier && (
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-[#1E2E5C] text-xs font-mono text-gray-300 truncate">
                Target: {targetIdentifier}
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">
                Feedback Type
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full bg-[#050811] border border-[#1E2E5C] rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-cyan-500"
              >
                <option value="FALSE_POSITIVE">False Positive (Marked safe item as threat)</option>
                <option value="FALSE_NEGATIVE">False Negative (Missed a genuine threat)</option>
                <option value="CORRECT_THREAT">Correct Threat (Verified detection)</option>
                <option value="INCORRECT_CATEGORY">Incorrect Classification Category</option>
                <option value="UNSURE">Unsure / Ambiguous</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">
                Your Assessment / Believed Label (Optional)
              </label>
              <input
                type="text"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                placeholder="e.g., Legitimate internal portal, Known scam template"
                className="w-full bg-[#050811] border border-[#1E2E5C] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">
                Explanation & Context
              </label>
              <textarea
                value={explanation}
                onChange={(e) => setExplanation(e.target.value)}
                rows={3}
                placeholder="Please describe why you believe this result is inaccurate or provide additional evidence..."
                className="w-full bg-[#050811] border border-[#1E2E5C] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            {/* Governance disclaimer */}
            <div className="flex items-start space-x-2 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-300">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>
                <strong>Safety Governance:</strong> Submissions are logged for human review and will not directly retrain active models without offline validation.
              </span>
            </div>

            {errorMsg && (
              <div className="p-2 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg">
                {errorMsg}
              </div>
            )}

            <div className="flex justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs font-medium text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 text-xs font-medium rounded-lg bg-cyan-500 text-black font-semibold hover:bg-cyan-400 disabled:opacity-50 transition-all shadow-[0_0_10px_rgba(0,240,255,0.3)]"
              >
                {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

