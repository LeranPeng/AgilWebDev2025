from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import csv
import io
from models import db, Tournament, Match, Player, Team
from utils import login_required, process_team, validate_match_players, get_or_create_player

# Create blueprint
tournament_bp = Blueprint('tournament', __name__)

@tournament_bp.route("/upload")
@login_required
def upload_page():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("html/upload.html")

@tournament_bp.route("/input_form")
@login_required
def input_form():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("html/InputForm.html")

@tournament_bp.route("/submit_results", methods=["POST"])
@login_required
def submit_results():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    try:
        # Get tournament details
        tournament_name = request.form.get("tournament_name")
        tournament_date_str = request.form.get("tournament_date")
        location = request.form.get("location", "")

        if not tournament_name or not tournament_date_str:
            flash("Tournament name and date are required")
            return redirect(url_for("tournament.input_form"))

        tournament_date = datetime.strptime(tournament_date_str, '%Y-%m-%d').date()

        # Create tournament
        tournament = Tournament(
            name=tournament_name,
            date=tournament_date,
            location=location,
            user_id=session["user_id"]
        )
        db.session.add(tournament)
        db.session.flush()  # Get the tournament ID without committing yet

        # Process match data
        rounds = request.form.getlist("round[]")
        groups = request.form.getlist("group[]")
        team1_names = request.form.getlist("team1[]")
        team2_names = request.form.getlist("team2[]")
        score1_list = request.form.getlist("score1[]")
        score2_list = request.form.getlist("score2[]")
        match_types = request.form.getlist("match_type[]")

        for i in range(len(rounds)):
            if i < len(team1_names) and i < len(team2_names) and i < len(score1_list) and i < len(
                    score2_list) and i < len(match_types):
                # Process teams
                team1 = process_team(team1_names[i])
                team2 = process_team(team2_names[i])

                # Add validation to prevent players appearing on both sides in doubles
                if match_types[i].endswith('Doubles') and not validate_match_players(team1, team2):
                    flash(f"Error: A player cannot be on both sides of the match (in match #{i + 1})")
                    return redirect(url_for("tournament.input_form"))

                group_name = groups[i] if i < len(groups) else ""

                # Create match
                match = Match(
                    tournament_id=tournament.id,
                    round_name=rounds[i],
                    group_name=group_name,
                    team1_id=team1.id,
                    team2_id=team2.id,
                    score1=score1_list[i],
                    score2=score2_list[i],
                    match_type=match_types[i]
                )
                db.session.add(match)

        # Commit all database changes
        db.session.commit()

        flash("Tournament results submitted successfully!")
        return redirect(url_for("user.dashboard"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error submitting results: {str(e)}")
        return redirect(url_for("tournament.input_form"))

@tournament_bp.route("/upload/pre", methods=["POST"])
@login_required
def upload_pre_tournament():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if 'pre_file' not in request.files:
        flash('No file part')
        return redirect(url_for("tournament.upload_page"))

    file = request.files['pre_file']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for("tournament.upload_page"))

    if file:
        # Process the CSV file
        try:
            # Read the CSV data
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_data = list(csv.reader(stream))

            # Validate and process data
            player_count = 0
            for row in csv_data[1:]:  # Skip header row
                if len(row) >= 1 and row[0]:
                    player = get_or_create_player(row[0])
                    player_count += 1

            db.session.commit()
            flash(f'Successfully imported {player_count} players!')
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing file: {str(e)}')

        return redirect(url_for('tournament.upload_page'))

@tournament_bp.route("/upload/post", methods=["POST"])
@login_required
def upload_post_tournament():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if 'post_file' not in request.files:
        flash('No file part')
        return redirect(url_for("tournament.upload_page"))

    file = request.files['post_file']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for("tournament.upload_page"))

    if file:
        try:
            # Save the file temporarily
            from flask import current_app
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Read the CSV data
            with open(filepath, 'r') as f:
                csv_reader = csv.reader(f)
                headers = next(csv_reader)
                matches = list(csv_reader)

            # Fixed template path - without the html/ prefix since it's in the templates/ directory
            return render_template('review_results.html', headers=headers, matches=matches, filename=filename)

        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(url_for('tournament.upload_page'))

@tournament_bp.route("/confirm_results/<filename>", methods=["POST"])
@login_required
def confirm_results(filename):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    try:
        tournament_name = request.form.get("tournament_name", f"Tournament from {filename}")
        tournament_date = datetime.now().date()

        # Create tournament
        tournament = Tournament(
            name=tournament_name,
            date=tournament_date,
            location=request.form.get("location", ""),
            user_id=session["user_id"]
        )
        db.session.add(tournament)
        db.session.flush()

        # Process the CSV file
        from flask import current_app
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(filename))
        with open(filepath, 'r') as f:
            csv_reader = csv.reader(f)
            headers = next(csv_reader)

            # Process each row in the CSV
            match_count = 0
            for row in csv_reader:
                if len(row) >= 4:  # Ensure row has enough data
                    try:
                        team1 = process_team(row[0])
                        team2 = process_team(row[1])

                        # Check if players appear on both sides
                        match_type = row[5] if len(row) > 5 else "Unknown"
                        if match_type.endswith('Doubles') and not validate_match_players(team1, team2):
                            flash(
                                f"Error: In doubles matches, players cannot appear on both sides (in {row[0]} vs {row[1]})")
                            return redirect(url_for('tournament.upload_page'))

                        match = Match(
                            tournament_id=tournament.id,
                            round_name=row[4] if len(row) > 4 else "Unknown",
                            team1_id=team1.id,
                            team2_id=team2.id,
                            score1=row[2] if len(row) > 2 else "0-0",
                            score2=row[3] if len(row) > 3 else "0-0",
                            match_type=row[5] if len(row) > 5 else "Unknown"
                        )
                        db.session.add(match)
                        match_count += 1
                    except Exception as e:
                        flash(f"Error processing match row: {str(e)}")
                        continue

        db.session.commit()
        os.remove(filepath)  # Clean up the temporary file

        flash(f'Successfully imported tournament with {match_count} matches!')
        return redirect(url_for('user.dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing results: {str(e)}')
        return redirect(url_for('tournament.upload_page'))

@tournament_bp.route("/api/matches/<int:tournament_id>")
@login_required
def get_matches(tournament_id):
    if "user_id" not in session:
        return jsonify({"error": "Not authorized"}), 401

    tournament = Tournament.query.filter_by(id=tournament_id, user_id=session["user_id"]).first()
    if not tournament:
        return jsonify({"error": "Tournament not found"}), 404

    matches = Match.query.filter_by(tournament_id=tournament_id).all()
    results = []

    for match in matches:
        team1_name = match.team1.player1.name
        if match.team1.player2:
            team1_name += f", {match.team1.player2.name}"

        team2_name = match.team2.player1.name
        if match.team2.player2:
            team2_name += f", {match.team2.player2.name}"

        results.append({
            "id": match.id,
            "round": match.round_name,
            "group": match.group_name,
            "team1": team1_name,
            "team2": team2_name,
            "score1": match.score1,
            "score2": match.score2,
            "match_type": match.match_type,
            "date": match.timestamp.strftime("%Y-%m-%d")
        })

    return jsonify(results)