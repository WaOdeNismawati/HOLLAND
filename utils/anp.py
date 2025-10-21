"""
ANP (Analytic Network Process) Module for Decision Support System
Integrates with RIASEC Holland test results to recommend college majors
"""

import numpy as np
import pandas as pd
from scipy.linalg import eig
import json


class ANPProcessor:
    def __init__(self):
        """Initialize ANP processor with RIASEC criteria and comprehensive major database"""
        
        # RIASEC criteria (6 Holland personality types)
        self.riasec_types = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
        
        # Comprehensive major database with RIASEC weights (0-1 scale)
        # Each major has weights for all 6 RIASEC types based on job market analysis and career requirements
        self.major_database = {
            # Engineering & Technology
            'Teknik Mesin': {'Realistic': 0.9, 'Investigative': 0.8, 'Artistic': 0.2, 'Social': 0.3, 'Enterprising': 0.4, 'Conventional': 0.7},
            'Teknik Informatika': {'Realistic': 0.6, 'Investigative': 0.9, 'Artistic': 0.5, 'Social': 0.4, 'Enterprising': 0.6, 'Conventional': 0.8},
            'Teknik Elektro': {'Realistic': 0.8, 'Investigative': 0.9, 'Artistic': 0.3, 'Social': 0.3, 'Enterprising': 0.5, 'Conventional': 0.7},
            'Teknik Sipil': {'Realistic': 0.9, 'Investigative': 0.7, 'Artistic': 0.4, 'Social': 0.5, 'Enterprising': 0.6, 'Conventional': 0.8},
            'Arsitektur': {'Realistic': 0.7, 'Investigative': 0.6, 'Artistic': 0.9, 'Social': 0.4, 'Enterprising': 0.5, 'Conventional': 0.6},
            'Teknik Industri': {'Realistic': 0.6, 'Investigative': 0.8, 'Artistic': 0.3, 'Social': 0.6, 'Enterprising': 0.8, 'Conventional': 0.9},
            
            # Health Sciences
            'Kedokteran': {'Realistic': 0.5, 'Investigative': 0.9, 'Artistic': 0.3, 'Social': 0.9, 'Enterprising': 0.4, 'Conventional': 0.7},
            'Farmasi': {'Realistic': 0.4, 'Investigative': 0.8, 'Artistic': 0.2, 'Social': 0.7, 'Enterprising': 0.5, 'Conventional': 0.9},
            'Keperawatan': {'Realistic': 0.5, 'Investigative': 0.6, 'Artistic': 0.3, 'Social': 0.9, 'Enterprising': 0.4, 'Conventional': 0.8},
            'Kesehatan Masyarakat': {'Realistic': 0.3, 'Investigative': 0.7, 'Artistic': 0.4, 'Social': 0.9, 'Enterprising': 0.6, 'Conventional': 0.7},
            
            # Business & Economics
            'Manajemen': {'Realistic': 0.3, 'Investigative': 0.5, 'Artistic': 0.4, 'Social': 0.8, 'Enterprising': 0.9, 'Conventional': 0.8},
            'Akuntansi': {'Realistic': 0.2, 'Investigative': 0.6, 'Artistic': 0.2, 'Social': 0.5, 'Enterprising': 0.6, 'Conventional': 0.9},
            'Ekonomi': {'Realistic': 0.3, 'Investigative': 0.8, 'Artistic': 0.3, 'Social': 0.6, 'Enterprising': 0.8, 'Conventional': 0.8},
            'Administrasi Bisnis': {'Realistic': 0.3, 'Investigative': 0.5, 'Artistic': 0.4, 'Social': 0.7, 'Enterprising': 0.9, 'Conventional': 0.9},
            'Keuangan dan Perbankan': {'Realistic': 0.2, 'Investigative': 0.7, 'Artistic': 0.2, 'Social': 0.6, 'Enterprising': 0.8, 'Conventional': 0.9},
            
            # Social Sciences & Education
            'Psikologi': {'Realistic': 0.2, 'Investigative': 0.8, 'Artistic': 0.5, 'Social': 0.9, 'Enterprising': 0.4, 'Conventional': 0.6},
            'Pendidikan': {'Realistic': 0.3, 'Investigative': 0.6, 'Artistic': 0.7, 'Social': 0.9, 'Enterprising': 0.5, 'Conventional': 0.7},
            'Sosiologi': {'Realistic': 0.2, 'Investigative': 0.8, 'Artistic': 0.5, 'Social': 0.9, 'Enterprising': 0.4, 'Conventional': 0.5},
            'Hubungan Internasional': {'Realistic': 0.2, 'Investigative': 0.7, 'Artistic': 0.4, 'Social': 0.8, 'Enterprising': 0.8, 'Conventional': 0.6},
            'Ilmu Komunikasi': {'Realistic': 0.3, 'Investigative': 0.5, 'Artistic': 0.8, 'Social': 0.9, 'Enterprising': 0.7, 'Conventional': 0.5},
            
            # Arts & Creative
            'Desain Komunikasi Visual': {'Realistic': 0.4, 'Investigative': 0.4, 'Artistic': 0.9, 'Social': 0.6, 'Enterprising': 0.6, 'Conventional': 0.4},
            'Seni Rupa': {'Realistic': 0.6, 'Investigative': 0.3, 'Artistic': 0.9, 'Social': 0.4, 'Enterprising': 0.4, 'Conventional': 0.3},
            'Desain Interior': {'Realistic': 0.7, 'Investigative': 0.4, 'Artistic': 0.9, 'Social': 0.5, 'Enterprising': 0.5, 'Conventional': 0.4},
            'Musik': {'Realistic': 0.4, 'Investigative': 0.3, 'Artistic': 0.9, 'Social': 0.6, 'Enterprising': 0.5, 'Conventional': 0.3},
            'Film dan Televisi': {'Realistic': 0.5, 'Investigative': 0.4, 'Artistic': 0.9, 'Social': 0.7, 'Enterprising': 0.7, 'Conventional': 0.4},
            
            # Science & Research
            'Matematika': {'Realistic': 0.2, 'Investigative': 0.9, 'Artistic': 0.3, 'Social': 0.3, 'Enterprising': 0.3, 'Conventional': 0.8},
            'Fisika': {'Realistic': 0.5, 'Investigative': 0.9, 'Artistic': 0.4, 'Social': 0.3, 'Enterprising': 0.3, 'Conventional': 0.7},
            'Kimia': {'Realistic': 0.6, 'Investigative': 0.9, 'Artistic': 0.2, 'Social': 0.3, 'Enterprising': 0.3, 'Conventional': 0.7},
            'Biologi': {'Realistic': 0.4, 'Investigative': 0.9, 'Artistic': 0.3, 'Social': 0.4, 'Enterprising': 0.3, 'Conventional': 0.6},
            'Statistika': {'Realistic': 0.2, 'Investigative': 0.9, 'Artistic': 0.3, 'Social': 0.4, 'Enterprising': 0.5, 'Conventional': 0.9},
            
            # Law & Public Service
            'Ilmu Hukum': {'Realistic': 0.2, 'Investigative': 0.8, 'Artistic': 0.4, 'Social': 0.8, 'Enterprising': 0.8, 'Conventional': 0.8},
            'Administrasi Publik': {'Realistic': 0.2, 'Investigative': 0.6, 'Artistic': 0.3, 'Social': 0.8, 'Enterprising': 0.7, 'Conventional': 0.9},
            'Ilmu Politik': {'Realistic': 0.2, 'Investigative': 0.8, 'Artistic': 0.5, 'Social': 0.8, 'Enterprising': 0.9, 'Conventional': 0.6},
            
            # Agriculture & Environment
            'Pertanian': {'Realistic': 0.8, 'Investigative': 0.7, 'Artistic': 0.3, 'Social': 0.5, 'Enterprising': 0.6, 'Conventional': 0.6},
            'Kehutanan': {'Realistic': 0.8, 'Investigative': 0.7, 'Artistic': 0.4, 'Social': 0.5, 'Enterprising': 0.5, 'Conventional': 0.6},
            'Lingkungan': {'Realistic': 0.6, 'Investigative': 0.8, 'Artistic': 0.4, 'Social': 0.7, 'Enterprising': 0.5, 'Conventional': 0.6},
            
            # Language & Literature
            'Sastra Indonesia': {'Realistic': 0.2, 'Investigative': 0.6, 'Artistic': 0.9, 'Social': 0.7, 'Enterprising': 0.4, 'Conventional': 0.4},
            'Sastra Inggris': {'Realistic': 0.2, 'Investigative': 0.6, 'Artistic': 0.9, 'Social': 0.8, 'Enterprising': 0.5, 'Conventional': 0.4},
            'Bahasa dan Sastra': {'Realistic': 0.2, 'Investigative': 0.7, 'Artistic': 0.8, 'Social': 0.8, 'Enterprising': 0.4, 'Conventional': 0.5},
        }
        
        # Equal weights for RIASEC criteria as requested
        self.criteria_weights = np.array([1/6] * 6)
    
    def calculate_priority(self, matrix):
        """
        Calculate priority vector from pairwise comparison matrix using eigenvalue method
        
        Args:
            matrix (np.array): Square pairwise comparison matrix
            
        Returns:
            np.array: Priority vector (normalized principal eigenvector)
        """
        # Calculate eigenvalues and eigenvectors
        eigenvalues, eigenvectors = eig(matrix)
        
        # Find principal eigenvalue (largest real eigenvalue)
        max_idx = np.argmax(eigenvalues.real)
        principal_eigenvector = eigenvectors[:, max_idx].real
        
        # Normalize to get priority vector
        priority_vector = principal_eigenvector / np.sum(principal_eigenvector)
        
        return np.abs(priority_vector)  # Ensure positive values
    
    def build_supermatrix(self, riasec_scores, major_weights):
        """
        Build ANP supermatrix with criteria (RIASEC) and alternatives (majors)
        
        Args:
            riasec_scores (dict): Student's RIASEC scores
            major_weights (dict): Major database with RIASEC weights
            
        Returns:
            tuple: (supermatrix, criteria_names, alternative_names)
        """
        criteria_names = self.riasec_types
        alternative_names = list(major_weights.keys())
        
        n_criteria = len(criteria_names)
        n_alternatives = len(alternative_names)
        matrix_size = n_criteria + n_alternatives
        
        # Initialize supermatrix
        supermatrix = np.zeros((matrix_size, matrix_size))
        
        # Fill criteria-to-criteria relationships (identity for independent criteria)
        criteria_matrix = np.eye(n_criteria) * self.criteria_weights.reshape(-1, 1)
        supermatrix[0:n_criteria, 0:n_criteria] = criteria_matrix
        
        # Fill alternative-to-criteria relationships (how alternatives relate to criteria)
        for i, major in enumerate(alternative_names):
            for j, criterion in enumerate(criteria_names):
                # Normalize major weights to sum to 1 for each criterion column
                weight = major_weights[major][criterion]
                supermatrix[n_criteria + i, j] = weight
        
        # Normalize columns to ensure stochastic matrix
        for j in range(matrix_size):
            col_sum = np.sum(supermatrix[:, j])
            if col_sum > 0:
                supermatrix[:, j] = supermatrix[:, j] / col_sum
        
        return supermatrix, criteria_names, alternative_names
    
    def limit_supermatrix(self, supermatrix, max_iterations=100, tolerance=1e-6):
        """
        Calculate limit supermatrix by raising to power until convergence
        
        Args:
            supermatrix (np.array): Initial supermatrix
            max_iterations (int): Maximum iterations for convergence
            tolerance (float): Convergence tolerance
            
        Returns:
            np.array: Limit supermatrix with stable priority weights
        """
        matrix = supermatrix.copy()
        
        for iteration in range(max_iterations):
            prev_matrix = matrix.copy()
            matrix = np.dot(matrix, matrix)  # Square the matrix
            
            # Check convergence
            if np.allclose(matrix, prev_matrix, atol=tolerance):
                break
        
        return matrix
    
    def recommend_majors(self, riasec_scores, major_map=None, comparison_matrix=None):
        """
        Generate final major recommendations using ANP methodology
        
        Args:
            riasec_scores (dict): Student's RIASEC test scores
            major_map (dict, optional): Custom major database (uses default if None)
            comparison_matrix (np.array, optional): Custom pairwise comparison (uses equal weights if None)
            
        Returns:
            dict: Comprehensive recommendation results
        """
        # Use provided major map or default database
        if major_map is None:
            major_map = self.major_database
        
        # Normalize student RIASEC scores (0-1 scale)
        max_score = max(riasec_scores.values()) if riasec_scores.values() else 1
        normalized_scores = {k: v/max_score for k, v in riasec_scores.items()}
        
        # Build supermatrix
        supermatrix, criteria_names, alternative_names = self.build_supermatrix(
            normalized_scores, major_map
        )
        
        # Calculate limit supermatrix
        limit_matrix = self.limit_supermatrix(supermatrix)
        
        # Extract final priorities for alternatives (majors)
        n_criteria = len(criteria_names)
        alternative_priorities = limit_matrix[n_criteria:, 0]  # First column gives final priorities
        
        # Calculate composite scores for ranking
        major_scores = {}
        for i, major in enumerate(alternative_names):
            # Weighted sum of major's RIASEC alignment with student scores
            composite_score = 0
            for criterion in self.riasec_types:
                student_strength = normalized_scores.get(criterion, 0)
                major_requirement = major_map[major][criterion]
                alignment = min(student_strength, major_requirement)  # Conservative alignment
                composite_score += alignment * self.criteria_weights[self.riasec_types.index(criterion)]
            
            # Combine with ANP priority
            final_score = (composite_score * 0.7) + (alternative_priorities[i] * 0.3)
            major_scores[major] = {
                'final_score': final_score,
                'anp_priority': alternative_priorities[i],
                'composite_score': composite_score,
                'riasec_alignment': {criterion: major_map[major][criterion] for criterion in self.riasec_types}
            }
        
        # Sort majors by final score
        ranked_majors = sorted(major_scores.items(), key=lambda x: x[1]['final_score'], reverse=True)
        
        # Prepare results
        results = {
            'top_5_majors': ranked_majors[:5],
            'all_majors_ranked': ranked_majors,
            'student_riasec_profile': normalized_scores,
            'anp_matrix_info': {
                'criteria': criteria_names,
                'alternatives': alternative_names,
                'supermatrix_size': supermatrix.shape
            },
            'methodology': 'ANP (Analytic Network Process) with RIASEC integration'
        }
        
        return results


# Convenience functions for backward compatibility and easy integration
def calculate_priority(matrix):
    """Standalone function to calculate priority vector from pairwise comparison matrix"""
    anp = ANPProcessor()
    return anp.calculate_priority(matrix)


def build_supermatrix(riasec_scores, major_weights):
    """Standalone function to build ANP supermatrix"""
    anp = ANPProcessor()
    return anp.build_supermatrix(riasec_scores, major_weights)


def limit_supermatrix(supermatrix, max_iterations=100, tolerance=1e-6):
    """Standalone function to calculate limit supermatrix"""
    anp = ANPProcessor()
    return anp.limit_supermatrix(supermatrix, max_iterations, tolerance)


def recommend_majors(riasec_scores, major_map=None, comparison_matrix=None):
    """Main function to get ANP-based major recommendations"""
    anp = ANPProcessor()
    return anp.recommend_majors(riasec_scores, major_map, comparison_matrix)


# Example usage and testing function
def test_anp_system():
    """Test the ANP system with sample data"""
    # Sample student RIASEC scores
    sample_scores = {
        'Realistic': 15,
        'Investigative': 20,
        'Artistic': 8,
        'Social': 12,
        'Enterprising': 10,
        'Conventional': 18
    }
    
    # Get recommendations
    results = recommend_majors(sample_scores)
    
    print("ANP System Test Results:")
    print("=" * 50)
    print(f"Student RIASEC Profile: {results['student_riasec_profile']}")
    print("\nTop 5 Recommended Majors:")
    for i, (major, data) in enumerate(results['top_5_majors'], 1):
        print(f"{i}. {major}: {data['final_score']:.3f}")
    
    return results


if __name__ == "__main__":
    # Run test if module is executed directly
    test_anp_system()