import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, X, Send, CheckCircle2 } from 'lucide-react';
import { submitFeedback } from '../api/client';
import { VerdictType } from '../types';

interface FeedbackModalProps {
  claimText: string;
  givenVerdict: VerdictType;
  onClose: () => void;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  claimText,
  givenVerdict,
  onClose
}) => {
  const [feedbackType, setFeedbackType] = useState<'helpful' | 'incorrect'>('helpful');
  const [suggestedVerdict, setSuggestedVerdict] = useState<string>('');
  const [comments, setComments] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await submitFeedback({
        claim_text: claimText,
        given_verdict: givenVerdict,
        feedback_type: feedbackType,
        suggested_verdict: suggestedVerdict || undefined,
        comments: comments || undefined
      });
      setSubmitted(true);
      setTimeout(() => {
        onClose();
      }, 1800);
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-4 text-white">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-base font-bold">Community Feedback Loop</h3>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {submitted ? (
          <div className="py-8 text-center space-y-2">
            <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
            <h4 className="text-lg font-bold text-white">Feedback Recorded</h4>
            <p className="text-xs text-slate-400">
              Thank you! Your feedback feeds our local heuristic scoring loop to improve future verification accuracy.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <span className="text-xs text-slate-400 block mb-1">Claim:</span>
              <p className="text-xs italic bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-slate-300 font-serif">
                "{claimText}"
              </p>
            </div>

            {/* Thumbs up/down toggle */}
            <div>
              <span className="text-xs font-semibold text-slate-300 block mb-2">How accurate was this check?</span>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setFeedbackType('helpful')}
                  className={`flex items-center justify-center space-x-2 py-2.5 rounded-xl border text-xs font-semibold transition-all ${
                    feedbackType === 'helpful'
                      ? 'bg-emerald-950/80 border-emerald-500 text-emerald-300'
                      : 'bg-slate-950 border-slate-800 text-slate-400'
                  }`}
                >
                  <ThumbsUp className="w-4 h-4" />
                  <span>Accurate / Helpful</span>
                </button>

                <button
                  type="button"
                  onClick={() => setFeedbackType('incorrect')}
                  className={`flex items-center justify-center space-x-2 py-2.5 rounded-xl border text-xs font-semibold transition-all ${
                    feedbackType === 'incorrect'
                      ? 'bg-rose-950/80 border-rose-500 text-rose-300'
                      : 'bg-slate-950 border-slate-800 text-slate-400'
                  }`}
                >
                  <ThumbsDown className="w-4 h-4" />
                  <span>Suggest Correction</span>
                </button>
              </div>
            </div>

            {feedbackType === 'incorrect' && (
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  What should the verdict be?
                </label>
                <select
                  value={suggestedVerdict}
                  onChange={(e) => setSuggestedVerdict(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white outline-none focus:border-sky-500"
                >
                  <option value="">Select recommended verdict...</option>
                  <option value="True">True</option>
                  <option value="False">False</option>
                  <option value="Misleading">Misleading</option>
                  <option value="Satire">Satire</option>
                  <option value="Unverified">Unverified</option>
                </select>
              </div>
            )}

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Additional Comments / Cited Evidence Link (Optional)
              </label>
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="Provide a source link or clarification note..."
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none focus:border-sky-500 resize-none"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex items-center space-x-1.5 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 transition-all disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{submitting ? 'Submitting...' : 'Submit Feedback'}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
