'use strict';

var gulp = require('gulp');
var del = require('del');
var rename = require("gulp-rename");
var runSequence = require('run-sequence');
var sass = require('gulp-sass');
var autoprefixer = require('gulp-autoprefixer');
var cssmin = require('gulp-cssmin')

var paths = gulp.paths;
var vendors = './scss/vendors/';

gulp.task('compile-vendors:clean', function () {
  return del([
    './vendors/css/**'
  ]);
});

gulp.task('compile-vendors:sass', function () {
  return gulp.src('./scss/vendors/**/*.scss')
  .pipe(sass().on('error', sass.logError))
  .pipe(autoprefixer())
  .pipe(rename({dirname: ''}))
  .pipe(gulp.dest('./vendors/css/'))
  .pipe(cssmin())
  .pipe(rename({suffix: '.min'}))
  .pipe(rename({dirname: ''}))
  .pipe(gulp.dest('./vendors/css/'));
});

gulp.task('compile-vendors', function(callback) {
  runSequence('compile-vendors:clean', 'compile-vendors:sass', callback);
});
