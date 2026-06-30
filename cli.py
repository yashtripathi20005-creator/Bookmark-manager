"""
Command Line Interface for the Bookmark Manager
"""
import click
import sys
from tabulate import tabulate
from datetime import datetime
from typing import List
from models import Bookmark
from database import Database
from utils import validate_url, get_valid_url, get_valid_tags, format_time_ago


class BookmarkCLI:
    """CLI interface for bookmark management"""

    def __init__(self):
        self.db = Database()

    def display_bookmarks(self, bookmarks: List[Bookmark], title: str = "Bookmarks"):
        """Display a list of bookmarks in a formatted table"""
        if not bookmarks:
            click.echo(f"\n✨ No bookmarks found.")
            return

        table_data = []
        for b in bookmarks:
            tags_str = ", ".join(b.tags) if b.tags else "-"
            status = "📌" if not b.is_archived else "📦"
            table_data.append([
                b.id,
                status,
                b.title[:40] + "..." if len(b.title) > 40 else b.title,
                b.url[:50] + "..." if len(b.url) > 50 else b.url,
                tags_str[:30] + "..." if len(tags_str) > 30 else tags_str,
                format_time_ago(b.updated_at)
            ])

        click.echo(f"\n📚 {title} ({len(bookmarks)} items)")
        click.echo(tabulate(
            table_data,
            headers=["ID", "", "Title", "URL", "Tags", "Updated"],
            tablefmt="simple",
            colalign=("left", "center", "left", "left", "left", "left")
        ))

    def display_stats(self):
        """Display bookmark statistics"""
        stats = self.db.get_bookmark_count()
        click.echo("\n📊 Statistics:")
        click.echo(f"  Total bookmarks: {stats['total']}")
        click.echo(f"  Active: {stats['active']}")
        click.echo(f"  Archived: {stats['archived']}")

        tags = self.db.get_all_tags()
        if tags:
            click.echo(f"  Unique tags: {len(tags)}")
            click.echo(f"  Tags: {', '.join(tags[:10])}{'...' if len(tags) > 10 else ''}")

    def prompt_for_bookmark_data(self, existing: Bookmark = None) -> Bookmark:
        """Interactive prompt for bookmark data"""
        click.echo("\n📝 Enter bookmark details:")

        if existing:
            url = click.prompt("URL", default=existing.url, show_default=True)
            title = click.prompt("Title", default=existing.title, show_default=True)
            description = click.prompt("Description", default=existing.description or "", show_default=True)
            tags = click.prompt("Tags (comma-separated)", default=", ".join(existing.tags), show_default=True)
        else:
            while True:
                url = click.prompt("URL")
                if validate_url(url):
                    break
                click.echo("❌ Invalid URL format. Please enter a valid URL (e.g., https://example.com)")

            title = click.prompt("Title")
            description = click.prompt("Description", default="")
            tags = click.prompt("Tags (comma-separated)", default="")

        tags_list = get_valid_tags(tags)

        if existing:
            existing.url = url
            existing.title = title
            existing.description = description if description else None
            existing.tags = tags_list
            return existing
        else:
            return Bookmark(
                id=None,
                url=url,
                title=title,
                description=description if description else None,
                tags=tags_list,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

    def add_command(self):
        """Add a new bookmark"""
        try:
            bookmark = self.prompt_for_bookmark_data()
            created = self.db.add_bookmark(bookmark)
            click.echo(f"\n✅ Bookmark added successfully! (ID: {created.id})")
        except Exception as e:
            click.echo(f"\n❌ Error adding bookmark: {e}", err=True)

    def list_command(self, include_archived: bool = False):
        """List all bookmarks"""
        bookmarks = self.db.get_all_bookmarks(include_archived)
        title = "All Bookmarks" if include_archived else "Active Bookmarks"
        self.display_bookmarks(bookmarks, title)
        self.display_stats()

    def search_command(self, query: str):
        """Search bookmarks"""
        if not query:
            click.echo("❌ Please provide a search query", err=True)
            return

        results = self.db.search_bookmarks(query)
        self.display_bookmarks(results, f"Search Results for '{query}'")

    def get_command(self, bookmark_id: int):
        """Get a specific bookmark by ID"""
        bookmark = self.db.get_bookmark_by_id(bookmark_id)
        if not bookmark:
            click.echo(f"\n❌ Bookmark with ID {bookmark_id} not found", err=True)
            return

        self.display_bookmarks([bookmark], f"Bookmark #{bookmark_id}")

    def update_command(self, bookmark_id: int):
        """Update a bookmark"""
        existing = self.db.get_bookmark_by_id(bookmark_id)
        if not existing:
            click.echo(f"\n❌ Bookmark with ID {bookmark_id} not found", err=True)
            return

        updated = self.prompt_for_bookmark_data(existing)
        self.db.update_bookmark(updated)
        click.echo(f"\n✅ Bookmark #{bookmark_id} updated successfully!")

    def delete_command(self, bookmark_id: int, force: bool = False):
        """Delete a bookmark"""
        bookmark = self.db.get_bookmark_by_id(bookmark_id)
        if not bookmark:
            click.echo(f"\n❌ Bookmark with ID {bookmark_id} not found", err=True)
            return

        if not force:
            click.echo(f"\nBookmark to delete:")
            self.display_bookmarks([bookmark], "Confirm Delete")
            if not click.confirm("Are you sure you want to delete this bookmark?"):
                click.echo("❌ Deletion cancelled")
                return

        self.db.delete_bookmark(bookmark_id)
        click.echo(f"\n✅ Bookmark #{bookmark_id} deleted successfully!")

    def archive_command(self, bookmark_id: int):
        """Archive a bookmark"""
        result = self.db.archive_bookmark(bookmark_id)
        if result:
            click.echo(f"\n✅ Bookmark #{bookmark_id} archived successfully!")
        else:
            click.echo(f"\n❌ Bookmark with ID {bookmark_id} not found", err=True)

    def unarchive_command(self, bookmark_id: int):
        """Unarchive a bookmark"""
        result = self.db.unarchive_bookmark(bookmark_id)
        if result:
            click.echo(f"\n✅ Bookmark #{bookmark_id} unarchived successfully!")
        else:
            click.echo(f"\n❌ Bookmark with ID {bookmark_id} not found", err=True)

    def tags_command(self):
        """List all tags"""
        tags = self.db.get_all_tags()
        if not tags:
            click.echo("\n✨ No tags found.")
            return

        click.echo("\n🏷️  All Tags:")
        for tag in tags:
            count = len(self.db.get_bookmarks_by_tag(tag))
            click.echo(f"  {tag} ({count} bookmark{'s' if count > 1 else ''})")

    def tag_command(self, tag: str, include_archived: bool = False):
        """Show bookmarks with a specific tag"""
        bookmarks = self.db.get_bookmarks_by_tag(tag, include_archived)
        self.display_bookmarks(bookmarks, f"Bookmarks tagged '{tag}'")

    def export_command(self, filename: str = "bookmarks_export.json"):
        """Export bookmarks to JSON"""
        try:
            data = self.db.export_to_json()
            import json
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            click.echo(f"\n✅ Bookmarks exported to {filename} ({len(data)} items)")
        except Exception as e:
            click.echo(f"\n❌ Error exporting bookmarks: {e}", err=True)

    def import_command(self, filename: str):
        """Import bookmarks from JSON"""
        try:
            import json
            with open(filename, 'r') as f:
                data = json.load(f)

            if not isinstance(data, list):
                click.echo("❌ Invalid JSON format. Expected a list of bookmarks.", err=True)
                return

            if not click.confirm(f"\nImport {len(data)} bookmarks from {filename}?"):
                click.echo("Import cancelled")
                return

            imported = self.db.import_from_json(data)
            click.echo(f"\n✅ Imported {imported} bookmarks from {filename}")
            if imported < len(data):
                click.echo(f"   Skipped {len(data) - imported} duplicate bookmarks")
        except FileNotFoundError:
            click.echo(f"\n❌ File {filename} not found", err=True)
        except json.JSONDecodeError:
            click.echo(f"\n❌ Invalid JSON in {filename}", err=True)
        except Exception as e:
            click.echo(f"\n❌ Error importing bookmarks: {e}", err=True)

    def clear_command(self, force: bool = False):
        """Clear all bookmarks"""
        if not force:
            if not click.confirm("\n⚠️  This will delete ALL bookmarks. Are you sure?"):
                click.echo("Operation cancelled")
                return
            if not click.confirm("⚠️  Are you absolutely sure? This cannot be undone!"):
                click.echo("Operation cancelled")
                return

        count = self.db.clear_all_bookmarks()
        click.echo(f"\n✅ Removed {count} bookmarks")

    def stats_command(self):
        """Display statistics"""
        self.display_stats()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """📚 Bookmark Manager with Tags - A powerful CLI tool to manage your bookmarks"""
    pass


@cli.command()
def add():
    """Add a new bookmark interactively"""
    cli_obj = BookmarkCLI()
    cli_obj.add_command()


@cli.command()
@click.option('--archived', is_flag=True, help='Include archived bookmarks')
def list(archived):
    """List all bookmarks"""
    cli_obj = BookmarkCLI()
    cli_obj.list_command(archived)


@cli.command()
@click.argument('query')
def search(query):
    """Search bookmarks by URL, title, description, or tags"""
    cli_obj = BookmarkCLI()
    cli_obj.search_command(query)


@cli.command()
@click.argument('bookmark_id', type=int)
def get(bookmark_id):
    """Get a specific bookmark by ID"""
    cli_obj = BookmarkCLI()
    cli_obj.get_command(bookmark_id)


@cli.command()
@click.argument('bookmark_id', type=int)
def update(bookmark_id):
    """Update a bookmark interactively"""
    cli_obj = BookmarkCLI()
    cli_obj.update_command(bookmark_id)


@cli.command()
@click.argument('bookmark_id', type=int)
@click.option('--force', is_flag=True, help='Skip confirmation')
def delete(bookmark_id, force):
    """Delete a bookmark"""
    cli_obj = BookmarkCLI()
    cli_obj.delete_command(bookmark_id, force)


@cli.command()
@click.argument('bookmark_id', type=int)
def archive(bookmark_id):
    """Archive a bookmark"""
    cli_obj = BookmarkCLI()
    cli_obj.archive_command(bookmark_id)


@cli.command()
@click.argument('bookmark_id', type=int)
def unarchive(bookmark_id):
    """Unarchive a bookmark"""
    cli_obj = BookmarkCLI()
    cli_obj.unarchive_command(bookmark_id)


@cli.command()
def tags():
    """List all tags"""
    cli_obj = BookmarkCLI()
    cli_obj.tags_command()


@cli.command()
@click.argument('tag')
@click.option('--archived', is_flag=True, help='Include archived bookmarks')
def tag(tag, archived):
    """Show bookmarks with a specific tag"""
    cli_obj = BookmarkCLI()
    cli_obj.tag_command(tag, archived)


@cli.command()
@click.option('--filename', default='bookmarks_export.json', help='Output filename')
def export(filename):
    """Export bookmarks to JSON"""
    cli_obj = BookmarkCLI()
    cli_obj.export_command(filename)


@cli.command()
@click.argument('filename')
def import_(filename):
    """Import bookmarks from JSON"""
    cli_obj = BookmarkCLI()
    cli_obj.import_command(filename)


@cli.command()
@click.option('--force', is_flag=True, help='Skip confirmation')
def clear(force):
    """Clear all bookmarks (dangerous)"""
    cli_obj = BookmarkCLI()
    cli_obj.clear_command(force)


@cli.command()
def stats():
    """Show bookmark statistics"""
    cli_obj = BookmarkCLI()
    cli_obj.stats_command()


if __name__ == '__main__':
    cli()
