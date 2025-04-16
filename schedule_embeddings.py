"""
Schedule embeddings generation as a background task
"""
import logging
import time
import sys
import subprocess
import os
from datetime import datetime
from app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('embeddings_scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_embeddings_generation(batch_size=50, delay=2, max_batches=2):
    """
    Run the embeddings generation script as a separate process
    
    Args:
        batch_size: Number of tenders to process in each batch
        delay: Seconds to wait between batches
        max_batches: Maximum number of batches to process per run
    """
    logger.info(f"Starting embeddings generation at {datetime.now()}")
    
    try:
        # Build the command with arguments
        cmd = [
            sys.executable,
            'generate_embeddings_incremental.py',
            '--batch-size', str(batch_size),
            '--delay', str(delay)
        ]
        
        if max_batches:
            cmd.extend(['--max-batches', str(max_batches)])
        
        # Run the process
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Set up environment
        env = os.environ.copy()
        
        # Start process
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Set a timeout (10 minutes)
        timeout = 600
        start_time = time.time()
        
        stdout = []
        stderr = []
        
        # Monitor the process with timeout
        while process.poll() is None:
            # Check for timeout
            if time.time() - start_time > timeout:
                process.terminate()
                logger.warning(f"Process timed out after {timeout} seconds")
                break
                
            # Read output
            if process.stdout:
                line = process.stdout.readline()
                if line:
                    stdout.append(line)
                    logger.info(f"Embeddings output: {line.strip()}")
            
            # Read errors
            if process.stderr:
                line = process.stderr.readline()
                if line:
                    stderr.append(line)
                    logger.error(f"Embeddings error: {line.strip()}")
            
            # Avoid busy waiting
            time.sleep(0.1)
        
        # Get final output and error
        stdout_output, stderr_output = process.communicate()
        if stdout_output:
            stdout.append(stdout_output)
        if stderr_output:
            stderr.append(stderr_output)
        
        # Check result
        if process.returncode == 0:
            logger.info("Embeddings generation completed successfully")
        else:
            logger.error(f"Embeddings generation failed with return code {process.returncode}")
            
        return process.returncode
        
    except Exception as e:
        logger.error(f"Error running embeddings generation: {str(e)}")
        return 1

if __name__ == "__main__":
    # This script can be run periodically (e.g., via cron or scheduler)
    # It will process embeddings in batches without overwhelming the API
    run_embeddings_generation(batch_size=50, delay=5, max_batches=3)