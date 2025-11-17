import os
import logging
import asyncio
import base64
from datetime import datetime
from collections import defaultdict
import gitlab
from gitlab.exceptions import GitlabAuthenticationError, GitlabError

logger = logging.getLogger(__name__)

class GitLabService:
    def __init__(self, config):
        self.config = config
        self.gl = None
        self._initializeGitLab()
    
    def _initializeGitLab(self):
        try:
            self.gl = gitlab.Gitlab('https://gitlab.com', private_token=self.config.gitlab_private_token)
            self.gl.auth()
            logger.info("GitLab API successfully authorized.")
        except GitlabAuthenticationError:
            logger.error("GitLab authentication error: check token")
        except GitlabError as e:
            logger.error(f"GitLab initialization error: {e}")
    
    def _getLanguageByFilename(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        return self.config.language_map.get(ext, None)
    
    async def _processProject(self, project):
        locStats = defaultdict(int)
        totalLines = 0
        try:
            tree = project.repository_tree(recursive=True, all=True)
            for item in tree:
                if item['type'] == 'blob':
                    filepath = item['path']
                    language = self._getLanguageByFilename(filepath)
                    if language is None:
                        continue
                    try:
                        fileContentBase64 = project.files.get(file_path=filepath, ref=project.default_branch).content
                        fileContent = base64.b64decode(fileContentBase64).decode('utf-8', errors='ignore')
                        lines = fileContent.splitlines()
                        numLines = min(len(lines), self.config.max_file_lines)
                        if numLines > 0:
                            locStats[language] += numLines
                            totalLines += numLines
                    except Exception as fileError:
                        logger.warning(f"Error processing file {filepath} in project {project.name}: {fileError}")
        except Exception as projectError:
            logger.error(f"Error processing project {project.name}: {projectError}")
        return locStats, totalLines
    
    def _getLastActivity(self, userProjects):
        latestCommitDate = None
        try:
            for project in userProjects:
                try:
                    commits = project.commits.list(per_page=1, all=False)
                    if commits:
                        commitDate = datetime.fromisoformat(commits[0].created_at.replace('Z', '+00:00'))
                        if latestCommitDate is None or commitDate > latestCommitDate:
                            latestCommitDate = commitDate
                except Exception as e:
                    logger.warning(f"Error getting commits for project {project.name}: {e}")
        except Exception as e:
            logger.error(f"Error getting last activity: {e}")
        
        if latestCommitDate:
            return latestCommitDate.strftime('%d\\.%m\\.%Y %H\\:%M')
        return "N/A"
    
    async def getStats(self):
        if not self.gl:
            return "*Error: GitLab API not initialized.*"
        
        finalStats = defaultdict(int)
        totalLoc = 0
        
        try:
            allProjects = self.gl.projects.list(owned=True, per_page=100, all=True)
            userProjects = [p for p in allProjects if p.namespace['kind'] == 'user']
            logger.info(f"Found {len(userProjects)} personal projects for user {self.config.target_gitlab_username}.")
            
            totalRepos = len(userProjects)
            publicRepos = sum(1 for p in userProjects if p.visibility == 'public')
            
            lastActivity = self._getLastActivity(userProjects)
            
            semaphore = asyncio.Semaphore(5)
            
            async def processWithSemaphore(project):
                async with semaphore:
                    return await self._processProject(project)
            
            tasks = [processWithSemaphore(project) for project in userProjects]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Task failed with exception: {result}")
                    continue
                locStats, projectTotalLines = result
                for lang, lines in locStats.items():
                    finalStats[lang] += lines
                totalLoc += projectTotalLines
        except Exception as e:
            logger.error(f"Critical error while collecting GitLab stats: {e}", exc_info=True)
            errorMessage = str(e).lower()
            if "tcp" in errorMessage or "health check" in errorMessage or "port 8000" in errorMessage:
                return "The host died :\\(\nCheck the logs in the host console\\. Or restart the bot instance\\."
            return "*Error: Could not collect GitLab stats.*"
        
        if totalLoc == 0:
            return f"*User {self.config.target_gitlab_username} has no code for analysis.*"
        
        percentageStats = {}
        for lang, lines in finalStats.items():
            percentage = (lines / totalLoc) * 100
            percentageStats[lang] = percentage
        
        sortedStats = sorted(percentageStats.items(), key=lambda item: item[1], reverse=True)
        
        totalLanguages = len(sortedStats)
        favoriteLanguage = sortedStats[0][0] if sortedStats else "N/A"
        
        outputLines = []
        for i, (lang, percent) in enumerate(sortedStats):
            if i >= self.config.max_displayed_languages:
                break
            outputLines.append(f"• {lang}: `{percent:.2f}%`")
        
        if not outputLines:
            return f"*Statistics for {self.config.target_gitlab_username}: no supported code found.*"
        
        def escapeMarkdown(text):
            for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
                text = text.replace(char, '\\' + char)
            return text
        
        escapedUsername = escapeMarkdown(self.config.target_gitlab_username)
        currentDate = datetime.now().strftime('%d\\.%m\\.%Y')
        currentTime = datetime.now().strftime('%H\\:%M')
        
        header = (
            f"*User statistics for {escapedUsername} on* [GitLab](https://gitlab\\.com/{self.config.target_gitlab_username})\n"
            f"*Total code lines:* `{totalLoc}`\n"
            f"*Last updated:* {currentDate} \\| {currentTime}\n"
            f"*Total languages:* `{totalLanguages}`\n"
            f"*Favorite language:* `{favoriteLanguage}`\n"
            f"*Repositories:* `{totalRepos}`\n"
            f"*Public repositories:* `{publicRepos}`\n"
            f"*Last activity:* {lastActivity}\n"
            f"\n*Languages*"
        )
        
        languagesText = "\n".join([f">{line}" for line in outputLines])
        
        return header + "\n" + languagesText