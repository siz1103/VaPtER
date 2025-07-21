import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Shield, AlertTriangle } from 'lucide-react';
import { fingerprintService } from '@/services/fingerprintService';
import { FingerprintDetail } from '@/types';

interface FingerprintResultsProps {
  scanId?: number;
  targetId?: number;
}

export default function FingerprintResults({ scanId, targetId }: FingerprintResultsProps) {
  const [fingerprints, setFingerprints] = useState<FingerprintDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFingerprints = async () => {
      try {
        setLoading(true);
        let data: FingerprintDetail[];
        
        if (scanId) {
          data = await fingerprintService.getByScan(scanId);
        } else if (targetId) {
          data = await fingerprintService.getByTarget(targetId, true);
        } else {
          throw new Error('Either scanId or targetId must be provided');
        }
        
        setFingerprints(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load fingerprint results');
      } finally {
        setLoading(false);
      }
    };

    fetchFingerprints();
  }, [scanId, targetId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8 text-red-500">
        <AlertTriangle className="h-5 w-5 mr-2" />
        {error}
      </div>
    );
  }

  if (fingerprints.length === 0) {
    return (
      <div className="text-center p-8 text-gray-500">
        No fingerprint results available
      </div>
    );
  }

  // Group fingerprints by host
  const groupedFingerprints = fingerprints.reduce((acc, fp) => {
    const host = fp.additional_info?.host || fp.target_address;
    if (!acc[host]) {
      acc[host] = [];
    }
    acc[host].push(fp);
    return acc;
  }, {} as Record<string, FingerprintDetail[]>);

  return (
    <div className="space-y-6">
      {Object.entries(groupedFingerprints).map(([host, hostFingerprints]) => (
        <Card key={host}>
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <Shield className="h-5 w-5 mr-2 text-blue-500" />
              {host}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-2 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">
                      Port
                    </th>
                    <th className="text-left py-2 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">
                      Service
                    </th>
                    <th className="text-left py-2 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">
                      Version
                    </th>
                    <th className="text-left py-2 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">
                      Confidence
                    </th>
                    <th className="text-left py-2 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">
                      Method
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {hostFingerprints
                    .sort((a, b) => a.port - b.port)
                    .map((fp) => {
                      const confidence = fingerprintService.getConfidenceLevel(fp.confidence_score);
                      return (
                        <tr key={fp.id} className="border-b border-gray-100 dark:border-gray-800">
                          <td className="py-2 px-4 text-sm">
                            <span className="font-mono">
                              {fingerprintService.formatPort(fp)}
                            </span>
                          </td>
                          <td className="py-2 px-4 text-sm">
                            {fp.service_name || 'Unknown'}
                          </td>
                          <td className="py-2 px-4 text-sm text-gray-600 dark:text-gray-400">
                            {fp.service_version || '-'}
                            {fp.service_product && fp.service_product !== fp.service_name && (
                              <span className="ml-1 text-xs">({fp.service_product})</span>
                            )}
                          </td>
                          <td className="py-2 px-4 text-sm">
                            <span className={`font-medium ${confidence.color}`}>
                              {fp.confidence_score}% ({confidence.label})
                            </span>
                          </td>
                          <td className="py-2 px-4 text-sm">
                            <Badge variant="outline" className="text-xs">
                              {fp.fingerprint_method}
                            </Badge>
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
            
            {/* Summary */}
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                <span>
                  Total ports scanned: {hostFingerprints.length}
                </span>
                <span>
                  Services identified: {hostFingerprints.filter(fp => fp.service_name).length}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}